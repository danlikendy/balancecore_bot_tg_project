from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.keyboards.menu import (
    get_main_menu_keyboard, get_cancel_keyboard, 
    get_confirm_keyboard, get_payment_methods_keyboard
)
from core.models.transaction import TransactionType
from core.config import settings
import re

router = Router()


class WithdrawStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_payment_method = State()
    waiting_for_payment_details = State()
    confirming_withdraw = State()


@router.callback_query(F.data == "withdraw")
async def callback_withdraw(callback: CallbackQuery, state: FSMContext, user: dict, balance_repo: dict, db: dict):
    """Начать процесс вывода средств"""
    from core.services.interest import InterestService
    
    interest_service = InterestService(db)
    deposits = interest_service.get_user_deposits(user.telegram_id)
    
    # Рассчитываем доступные средства
    available_balance = user.balance
    available_deposits = 0.0
    
    for deposit in deposits:
        if deposit.is_active:
            # Применяем текущие проценты
            current_interest = deposit.calculate_interest()
            available_deposits += deposit.current_amount + current_interest
    
    total_available = available_balance + available_deposits
    
    # Проверяем общую доступную сумму
    if total_available <= 0:
        await callback.message.edit_text(
            "<b>Недостаточно средств</b>\n\nУ вас нет доступных средств для вывода.\nСначала пополните баланс.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    # Проверяем минимальную сумму
    if total_available < settings.min_withdrawal_amount:
        await callback.message.edit_text(
            f"<b>Недостаточно средств</b>\n\n"
            f"Доступно: {total_available:.2f} руб.\n"
            f"Минимальная сумма вывода: {settings.min_withdrawal_amount} руб.",
            reply_markup=get_main_menu_keyboard()
        )
        await callback.answer()
        return
    
    await state.set_state(WithdrawStates.waiting_for_amount)
    
    withdraw_text = f"""
<b>Вывод средств</b>

Доступно с баланса: <b>{available_balance:.2f} руб.</b>
Доступно с депозитов: <b>{available_deposits:.2f} руб.</b>
Общая сумма: <b>{total_available:.2f} руб.</b>

Минимальная сумма: <b>{settings.min_withdrawal_amount} руб.</b>
Комиссия администратора: <b>{settings.admin_percentage}%</b>

Введите сумму для вывода (только число):
Например: 1000 или 500.50
    """
    
    await callback.message.edit_text(
        withdraw_text,
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(WithdrawStates.waiting_for_amount)
async def process_withdraw_amount(message: Message, state: FSMContext, user: dict):
    """Обработка суммы вывода"""
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
        
        if amount < settings.min_withdrawal_amount:
            await message.answer(
                f"Минимальная сумма вывода: {settings.min_withdrawal_amount} руб. "
                "Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        if amount > user.balance:
            await message.answer(
                f"Недостаточно средств. Ваш баланс: {user.balance:.2f} руб. "
                "Попробуйте еще раз:",
                reply_markup=get_cancel_keyboard()
            )
            return
        
        # Сохраняем сумму
        await state.update_data(amount=amount)
        await state.set_state(WithdrawStates.waiting_for_payment_method)
        
        await message.answer(
            f"Сумма: <b>{amount:.2f} руб.</b>\n\n"
            "Выберите способ получения средств:",
            reply_markup=get_payment_methods_keyboard()
        )
        
    except ValueError:
        await message.answer(
            "Неверный формат суммы. Введите только число:\n"
            "Например: 1000 или 500.50",
            reply_markup=get_cancel_keyboard()
        )


@router.callback_query(F.data.startswith("payment_"), WithdrawStates.waiting_for_payment_method)
async def process_payment_method(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора способа оплаты"""
    payment_method_map = {
        "payment_card": "Банковская карта",
        "payment_bank": "Банковский перевод",
        "payment_wallet": "Электронный кошелек"
    }
    
    payment_method = payment_method_map.get(callback.data)
    if not payment_method:
        await callback.answer("Неверный способ оплаты")
        return
    
    await state.update_data(payment_method=payment_method)
    await state.set_state(WithdrawStates.waiting_for_payment_details)
    
    details_text = f"""
<b>Способ получения: {payment_method}</b>

Введите реквизиты для получения средств:

<b>Для банковской карты:</b> номер карты, ФИО
<b>Для банковского перевода:</b> номер счета, БИК, ФИО
<b>Для электронного кошелька:</b> номер кошелька, ФИО

Например: 1234 5678 9012 3456, Иванов Иван Иванович
    """
    
    await callback.message.edit_text(
        details_text,
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()


@router.message(WithdrawStates.waiting_for_payment_details)
async def process_payment_details(message: Message, state: FSMContext):
    """Обработка реквизитов"""
    payment_details = message.text.strip()
    
    if len(payment_details) < 10:
        await message.answer(
            "Реквизиты слишком короткие. Введите полные реквизиты:",
            reply_markup=get_cancel_keyboard()
        )
        return
    
    await state.update_data(payment_details=payment_details)
    await state.set_state(WithdrawStates.confirming_withdraw)
    
    data = await state.get_data()
    amount = data['amount']
    payment_method = data['payment_method']
    admin_fee = amount * (settings.admin_percentage / 100)
    final_amount = amount - admin_fee
    
    confirm_text = f"""
<b>Подтверждение вывода</b>

Сумма к выводу: <b>{amount:.2f} руб.</b>
Способ получения: <b>{payment_method}</b>
Реквизиты: <b>{payment_details}</b>

<b>Расчет комиссии:</b>
• Сумма: {amount:.2f} руб.
• Комиссия ({settings.admin_percentage}%): {admin_fee:.2f} руб.
• К получению: <b>{final_amount:.2f} руб.</b>

<b>Внимание:</b> Заявка будет рассмотрена администратором.
Подтвердите создание заявки:
    """
    
    await message.answer(
        confirm_text,
        reply_markup=get_confirm_keyboard()
    )


@router.callback_query(F.data == "confirm", WithdrawStates.confirming_withdraw)
async def confirm_withdraw(callback: CallbackQuery, state: FSMContext, balance_repo: dict, user: dict, db: dict):
    """Подтверждение вывода"""
    from core.services.interest import InterestService
    
    data = await state.get_data()
    amount = data['amount']
    payment_method = data['payment_method']
    payment_details = data['payment_details']
    
    try:
        interest_service = InterestService(db)
        deposits = interest_service.get_user_deposits(user.telegram_id)
        
        # Рассчитываем, сколько нужно взять с депозитов и с баланса
        remaining_amount = amount
        deposits_to_close = []
        
        # Сначала берем с депозитов
        for deposit in deposits:
            if deposit.is_active and remaining_amount > 0:
                # Применяем текущие проценты
                current_interest = deposit.calculate_interest()
                deposit.apply_interest()
                
                if deposit.current_amount <= remaining_amount:
                    # Закрываем весь депозит
                    deposits_to_close.append(deposit)
                    remaining_amount -= deposit.current_amount
                else:
                    # Частично закрываем депозит (пока не реализовано)
                    remaining_amount = 0
                    break
        
        # Закрываем депозиты
        for deposit in deposits_to_close:
            interest_service.close_deposit(deposit.id)
        
        # Создаем заявку на вывод
        withdraw_request = balance_repo.create_withdraw_request(
            user_id=user.telegram_id,
            amount=amount,
            payment_method=payment_method,
            payment_details=payment_details
        )
        
        admin_fee = amount * (settings.admin_percentage / 100)
        final_amount = amount - admin_fee
        
        success_text = f"""
<b>Заявка на вывод создана!</b>

ID заявки: <b>{withdraw_request.id}</b>
Сумма: <b>{amount:.2f} руб.</b>
Способ: <b>{payment_method}</b>
Реквизиты: <b>{payment_details}</b>

<b>Расчет:</b>
• Комиссия ({settings.admin_percentage}%): {admin_fee:.2f} руб.
• К получению: <b>{final_amount:.2f} руб.</b>

<b>Статус:</b> Ожидает рассмотрения администратором

Заявка будет обработана в ближайшее время.
        """
        
        await callback.message.edit_text(
            success_text,
            reply_markup=get_main_menu_keyboard()
        )
        
    except Exception as e:
        error_text = f"""
<b>Ошибка при создании заявки</b>

Произошла ошибка: {str(e)}

Попробуйте еще раз или обратитесь к администратору.
        """
        
        await callback.message.edit_text(
            error_text,
            reply_markup=get_main_menu_keyboard()
        )
    
    await state.clear()
    await callback.answer()


@router.callback_query(F.data == "cancel", WithdrawStates)
async def cancel_withdraw(callback: CallbackQuery, state: FSMContext):
    """Отмена вывода"""
    await state.clear()
    await callback.message.edit_text(
        "Вывод отменен",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer("Вывод отменен")
