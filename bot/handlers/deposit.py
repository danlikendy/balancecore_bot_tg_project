from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.keyboards.menu import get_main_menu_keyboard, get_cancel_keyboard, get_confirm_keyboard, get_payment_methods_keyboard
from core.models.transaction import TransactionType
from core.services.payment import yookassa_service
from core.models.payment import Payment, PaymentStatus, PaymentMethod
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


@router.callback_query(F.data.startswith("payment_"), DepositStates.waiting_for_payment_method)
async def process_payment_method(callback: CallbackQuery, state: FSMContext, user: dict, db: dict):
    """Обработка выбора способа оплаты"""
    payment_method_map = {
        "payment_card": PaymentMethod.BANK_CARD,
        "payment_yoomoney": PaymentMethod.YOO_MONEY,
        "payment_qiwi": PaymentMethod.QIWI,
        "payment_webmoney": PaymentMethod.WEBMONEY,
        "payment_alfabank": PaymentMethod.ALFABANK,
        "payment_sberbank": PaymentMethod.SBERBANK
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
    
    confirm_text = f"""
<b>Подтверждение пополнения</b>

Сумма: <b>{amount:.2f} руб.</b>
Описание: {description or 'Не указано'}
Способ оплаты: <b>{payment_method.value}</b>

Подтвердите создание платежа:
    """
    
    await callback.message.edit_text(
        confirm_text,
        reply_markup=get_confirm_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "confirm", DepositStates.confirming_deposit)
async def confirm_deposit(callback: CallbackQuery, state: FSMContext, balance_repo: dict, user: dict):
    """Подтверждение пополнения"""
    data = await state.get_data()
    amount = data['amount']
    description = data.get('description')
    
    try:
        # Создаем транзакцию
        transaction = balance_repo.create_transaction(
            user_id=user.telegram_id,
            amount=amount,
            transaction_type="deposit",
            description=description
        )
        
        # Обновляем баланс
        success = balance_repo.update_user_balance(user.telegram_id, amount)
        
        if success:
            # Завершаем транзакцию
            balance_repo.complete_transaction(transaction.id)
            
            success_text = f"""
<b>Пополнение успешно!</b>

Сумма: <b>{amount:.2f} руб.</b>
Описание: {description or 'Не указано'}
ID транзакции: {transaction.id}

Ваш новый баланс: <b>{user.balance + amount:.2f} руб.</b>
            """
            
            await callback.message.edit_text(
                success_text,
                reply_markup=get_main_menu_keyboard()
            )
        else:
            raise Exception("Failed to update balance")
            
    except Exception as e:
        error_text = f"""
<b>Ошибка при пополнении</b>

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
