from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.keyboards.menu import get_main_menu_keyboard, get_cancel_keyboard, get_confirm_keyboard, get_payment_methods_keyboard
from core.models.transaction import TransactionType
from core.services.payment import yookassa_service
from core.services.paymaster import PayMasterService
from core.services.ozon import OzonPayService
from core.services.interest import InterestService
from core.models.payment import Payment, PaymentStatus, PaymentMethod
from datetime import datetime
import re

router = Router()


class DepositStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_description = State()
    waiting_for_payment_method = State()
    confirming_deposit = State()
    processing_payment = State()


@router.callback_query(F.data == "deposit")
async def callback_deposit(callback: CallbackQuery, state: FSMContext):
    """Начать процесс пополнения"""
    await state.set_state(DepositStates.waiting_for_amount)
    
    deposit_text = """
<b>Пополнение баланса</b>

Введите сумму для пополнения (только число):
Например: 1000 или 500.50
    """
    
    await callback.message.edit_text(
        deposit_text,
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(DepositStates.waiting_for_amount)
async def process_deposit_amount(message: Message, state: FSMContext):
    """Обработка суммы пополнения"""
    try:
        # Парсим сумму
        amount_text = message.text.replace(',', '.').strip()
        amount = float(amount_text)
        
        if amount <= 0:
            await message.answer(
                "Сумма должна быть больше нуля. Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        if amount > 1000000:  # Максимальная сумма
            await message.answer(
                "Сумма слишком большая. Максимум: 1,000,000 руб. Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Сохраняем сумму
        await state.update_data(amount=amount)
        await state.set_state(DepositStates.waiting_for_description)
        
        await message.answer(
            f"Сумма: <b>{amount:.2f} руб.</b>\n\n"
            "Введите описание пополнения (необязательно):\n"
            "Например: Пополнение через карту",
            reply_markup=get_cancel_keyboard()
        )
        
    except ValueError:
        await message.answer(
            "Неверный формат суммы. Введите только число:\n"
            "Например: 1000 или 500.50",
            reply_markup=get_cancel_keyboard()
        )


@router.message(DepositStates.waiting_for_description)
async def process_deposit_description(message: Message, state: FSMContext):
    """Обработка описания пополнения"""
    description = message.text.strip() if message.text else None
    await state.update_data(description=description)
    await state.set_state(DepositStates.waiting_for_payment_method)
    
    data = await state.get_data()
    amount = data['amount']
    
    payment_text = f"""
<b>Выбор способа оплаты</b>

Сумма: <b>{amount:.2f} руб.</b>
Описание: {description or 'Не указано'}

Выберите способ оплаты:
    """
    
    await message.answer(
        payment_text,
        reply_markup=get_payment_methods_keyboard()
    )


@router.callback_query(F.data.startswith("payment_method_"), DepositStates.waiting_for_payment_method)
async def process_payment_method(callback: CallbackQuery, state: FSMContext, user: dict, db: dict):
    """Обработка выбора способа оплаты"""
    payment_method_map = {
        "payment_method_yookassa": "yookassa",
        "payment_method_paymaster": "paymaster", 
        "payment_method_ozon": "ozon",
    }
    
    payment_method = payment_method_map.get(callback.data)
    if not payment_method:
        await callback.answer("Неверный способ оплаты")
        return
    
    await state.update_data(payment_method=payment_method)
    await state.set_state(DepositStates.confirming_deposit)
    
    data = await state.get_data()
    amount = data['amount']
    description = data.get('description')
    
    # Получаем название сервиса
    service_names = {
        "yookassa": "YooKassa",
        "paymaster": "PayMaster",
        "ozon": "Ozon Pay"
    }
    service_name = service_names.get(payment_method, payment_method)
    
    confirm_text = f"""
<b>Подтверждение пополнения</b>

Сумма: <b>{amount:.2f} руб.</b>
Описание: {description or 'Не указано'}
Способ оплаты: <b>{service_name}</b>

Подтвердите создание платежа:
    """
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=get_confirm_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "confirm", DepositStates.confirming_deposit)
async def confirm_deposit(callback: CallbackQuery, state: FSMContext, balance_repo: dict, user: dict, db: dict):
    """Подтверждение пополнения"""
    data = await state.get_data()
    amount = data['amount']
    description = data.get('description')
    payment_method = data.get('payment_method')
    
    try:
        # Выбираем сервис в зависимости от способа оплаты
        from core.config import settings
        
        if payment_method == "paymaster":
            payment_service = PayMasterService(settings)
            service_name = "PayMaster"
        elif payment_method == "ozon":
            payment_service = OzonPayService(settings)
            service_name = "Ozon Pay"
        else:
            payment_service = yookassa_service
            service_name = "YooKassa"
        
        # Создаем платеж
        payment_result = payment_service.create_payment(
            amount=amount,
            description=description or f"Пополнение депозита пользователя {user.telegram_id}",
            user_id=user.telegram_id
        )
        
        if not payment_result["success"]:
            raise Exception(payment_result["error"])
        
        # Создаем запись о платеже в БД
        payment = Payment(
            user_id=user.telegram_id,
            amount=amount,
            description=description,
            payment_method=payment_method,
            status=PaymentStatus.PENDING,
            yookassa_payment_id=payment_result["payment_id"],
            yookassa_confirmation_url=payment_result.get("payment_url")
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        
        # Создаем транзакцию
        transaction = balance_repo.create_transaction(
            user_id=user.telegram_id,
            amount=amount,
            transaction_type="deposit",
            description=description or f"Пополнение через PayMaster (ID: {payment.id})"
        )
        
        # Показываем ссылку для оплаты
        payment_text = f"""
<b>Платеж создан!</b>

Сумма: <b>{amount:.2f} руб.</b>
Описание: {description or 'Не указано'}
Способ оплаты: <b>{service_name}</b>

<b>Для оплаты:</b>
1. Перейдите по ссылке ниже
2. Выберите удобный способ оплаты
3. Подтвердите платеж
4. Деньги поступят на депозит автоматически

<a href="{payment_result['payment_url']}">💳 Оплатить через {service_name}</a>

ID платежа: <b>{payment_result['payment_id']}</b>
        """
        
        if payment_result.get("qr_code"):
            payment_text += f"\n\n📱 Или отсканируйте QR-код:\n{payment_result['qr_code']}"
        
        await callback.message.edit_text(
            payment_text,
            reply_markup=get_main_menu_keyboard()
        )
            
    except Exception as e:
        error_text = f"""
<b>Ошибка при создании платежа</b>

Произошла ошибка: {str(e)}

Попробуйте еще раз или обратитесь к администратору.
        """
        
        await callback.message.edit_text(
            error_text,
            reply_markup=get_main_menu_keyboard()
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel", DepositStates)
async def cancel_deposit(callback: CallbackQuery, state: FSMContext):
    """Отмена пополнения"""
    await state.clear()
    await callback.message.edit_text(
        "Пополнение отменено",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer("Пополнение отменено")
