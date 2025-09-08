from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню бота"""
    keyboard = [
        [InlineKeyboardButton(text="Мой баланс", callback_data="balance")],
        [InlineKeyboardButton(text="Пополнить", callback_data="deposit")],
        [InlineKeyboardButton(text="Вывести средства", callback_data="withdraw")],
        [InlineKeyboardButton(text="История операций", callback_data="history")],
    ]
    
    if is_admin:
        keyboard.append([InlineKeyboardButton(text="Админ-панель", callback_data="admin")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура отмены"""
    keyboard = [
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton(text="Подтвердить", callback_data="confirm"),
            InlineKeyboardButton(text="Отмена", callback_data="cancel")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_payment_methods_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты"""
    keyboard = [
        [InlineKeyboardButton(text="Банковская карта", callback_data="payment_card")],
        [InlineKeyboardButton(text="ЮMoney", callback_data="payment_yoomoney")],
        [InlineKeyboardButton(text="QIWI Кошелек", callback_data="payment_qiwi")],
        [InlineKeyboardButton(text="WebMoney", callback_data="payment_webmoney")],
        [InlineKeyboardButton(text="Альфа-Клик", callback_data="payment_alfabank")],
        [InlineKeyboardButton(text="Сбербанк Онлайн", callback_data="payment_sberbank")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Админ-клавиатура"""
    keyboard = [
        [InlineKeyboardButton(text="Ожидающие заявки", callback_data="admin_pending")],
        [InlineKeyboardButton(text="Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)
