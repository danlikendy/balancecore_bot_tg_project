from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from bot.keyboards.menu import get_main_menu_keyboard, get_admin_keyboard
from core.config import settings

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, user: dict, is_admin: bool):
    """Обработчик команды /start"""
    welcome_text = f"""
<b>Добро пожаловать в BalanceCore!</b>

Привет, {message.from_user.first_name}! 

Этот бот поможет вам управлять вашим балансом:
• Пополнять средства
• Выводить деньги с процентами
• Отслеживать операции

Ваш текущий баланс: <b>{user.balance:.2f} руб.</b>

Выберите действие:
    """
    
    await message.answer(
        welcome_text,
        reply_markup=get_main_menu_keyboard(is_admin)
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
<b>Доступные команды:</b>

/start - Главное меню
/balance - Мой баланс
/deposit - Пополнить баланс
/withdraw - Вывести средства
/history - История операций
/help - Эта справка

<b>Как пользоваться ботом:</b>
1. Пополните баланс через меню
2. Дождитесь обработки (обычно мгновенно)
3. Выводите средства с комиссией {admin_percentage}%
4. Заявки на вывод обрабатываются администратором

<b>Важно:</b>
• Минимальная сумма вывода: {min_withdrawal} руб.
• Задержка вывода: {withdrawal_delay} дней после пополнения
• Комиссия администратора: {admin_percentage}%

По всем вопросам обращайтесь к администратору.
    """.format(
        admin_percentage=settings.admin_percentage,
        min_withdrawal=settings.min_withdrawal_amount,
        withdrawal_delay=settings.withdrawal_delay_days
    )
    
    await message.answer(help_text)


@router.callback_query(F.data == "main_menu")
async def callback_main_menu(callback: CallbackQuery, user: dict, is_admin: bool):
    """Возврат в главное меню"""
    await callback.message.edit_text(
        "<b>Главное меню</b>\n\nВыберите действие:",
        reply_markup=get_main_menu_keyboard(is_admin)
    )
    await callback.answer()


@router.callback_query(F.data == "balance")
async def callback_balance(callback: CallbackQuery, user: dict):
    """Показать баланс"""
    balance_text = f"""
<b>Ваш баланс</b>

Текущий баланс: <b>{user.balance:.2f} руб.</b>

Доступно для вывода: <b>{user.balance:.2f} руб.</b>
    """
    
    await callback.message.edit_text(
        balance_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "history")
async def callback_history(callback: CallbackQuery, balance_repo: dict, user: dict):
    """Показать историю операций"""
    transactions = balance_repo.get_user_transactions(user.telegram_id, limit=10)
    
    if not transactions:
        history_text = "<b>История операций</b>\n\nОпераций пока нет."
    else:
        history_text = "<b>История операций</b>\n\n"
        for transaction in transactions:
            status_text = "Завершено" if transaction.status == "completed" else "В обработке"
            type_text = "Пополнение" if transaction.transaction_type == "deposit" else "Вывод"
            
            history_text += f"{status_text} {type_text} {transaction.amount:+.2f} руб.\n"
            if transaction.description:
                history_text += f"   Описание: {transaction.description}\n"
            history_text += f"   Дата: {transaction.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await callback.message.edit_text(
        history_text,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin")
async def callback_admin(callback: CallbackQuery, is_admin: bool):
    """Админ-панель"""
    if not is_admin:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    admin_text = """
<b>Админ-панель</b>

Выберите действие:
    """
    
    await callback.message.edit_text(
        admin_text,
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_pending")
async def callback_admin_pending(callback: CallbackQuery, balance_repo: dict, is_admin: bool):
    """Ожидающие заявки"""
    if not is_admin:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    pending_requests = balance_repo.get_pending_withdraw_requests()
    
    if not pending_requests:
        admin_text = "<b>Ожидающие заявки</b>\n\nЗаявок нет."
    else:
        admin_text = f"<b>Ожидающие заявки</b>\n\nНайдено: {len(pending_requests)} заявок\n\n"
        
        for request in pending_requests[:5]:  # Показываем первые 5
            admin_text += f"ID: {request.id}\n"
            admin_text += f"Пользователь: {request.user_id}\n"
            admin_text += f"Сумма: {request.amount:.2f} руб.\n"
            admin_text += f"Способ: {request.payment_method}\n"
            admin_text += f"Дата: {request.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
    
    await callback.message.edit_text(
        admin_text,
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def callback_admin_users(callback: CallbackQuery, is_admin: bool):
    """Управление пользователями"""
    if not is_admin:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    admin_text = """
<b>Управление пользователями</b>

Для детального управления пользователями используйте веб-интерфейс:
http://localhost:8000/admin/users
    """
    
    await callback.message.edit_text(
        admin_text,
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def callback_admin_stats(callback: CallbackQuery, balance_repo: dict, is_admin: bool):
    """Статистика"""
    if not is_admin:
        await callback.answer("У вас нет прав администратора", show_alert=True)
        return
    
    # Получаем базовую статистику
    pending_requests = balance_repo.get_pending_withdraw_requests()
    
    stats_text = f"""
<b>Статистика</b>

Ожидающих заявок: {len(pending_requests)}
Процент админа: {settings.admin_percentage}%
Мин. сумма вывода: {settings.min_withdrawal_amount} руб.
Задержка вывода: {settings.withdrawal_delay_days} дней

Для детальной статистики используйте веб-интерфейс:
http://localhost:8000/admin
    """
    
    await callback.message.edit_text(
        stats_text,
        reply_markup=get_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "cancel")
async def callback_cancel(callback: CallbackQuery, state: FSMContext):
    """Отмена операции"""
    await state.clear()
    await callback.message.edit_text(
        "Операция отменена",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer("Операция отменена")
