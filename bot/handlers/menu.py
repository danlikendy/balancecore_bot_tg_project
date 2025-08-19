from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
import httpx
from core.config import settings

router = Router()

def main_kb():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Баланс"), KeyboardButton(text="Тарифы")],
            [KeyboardButton(text="Вывод"), KeyboardButton(text="FAQ")],
        ],
        resize_keyboard=True
    )

def get_user_id(msg: Message) -> int:
    # в ЛС from_user есть, в редких случаях подстрахуемся chat.id
    return (msg.from_user.id if msg.from_user else msg.chat.id)

@router.message(F.text == "/start")
async def start(msg: Message):
    await msg.answer("BalanceCore Bot is running. Выберите пункт меню.", reply_markup=main_kb())

@router.message(F.text == "Баланс")
async def balance(msg: Message):
    user_id = get_user_id(msg)
    async with httpx.AsyncClient(base_url=settings.API_BASE_URL, timeout=10) as c:
        r = await c.get(f"/users/{user_id}/balance")
        r.raise_for_status()
        data = r.json()
    await msg.answer(f"Ваш баланс: {data['balance']:.2f} ₽")

@router.message(F.text == "Тарифы")
async def tariffs(msg: Message):
    async with httpx.AsyncClient(base_url=settings.API_BASE_URL, timeout=10) as c:
        r = await c.get("/tariffs")
        r.raise_for_status()
        tariffs = r.json()
    lines = [f"• {t['name']} (мин. {t['min_amount']} ₽)" for t in tariffs]
    await msg.answer("Доступные тарифы:\n" + "\n".join(lines))

@router.message(F.text == "Вывод")
async def withdraw_entry(msg: Message):
    await msg.answer(
        "Введите сумму и реквизиты в формате:\n`1000; карта ****1234`",
        parse_mode="Markdown"
    )

# обработчик с регуляркой сработает только для текстовых сообщений, но подстрахуемся
@router.message(F.text.regexp(r"^\s*\d+(\.\d+)?\s*;\s*.+$"))
async def withdraw_request(msg: Message):
    if not msg.text:
        await msg.answer("Ожидаю текст вида: `1000; карта ****1234`", parse_mode="Markdown")
        return

    try:
        amount_str, dest = msg.text.split(";", 1)
        amount = float(amount_str.strip())
        dest = dest.strip()
        if amount <= 0 or not dest:
            raise ValueError
    except Exception:
        await msg.answer("Формат неверный. Пример: `1000; карта ****1234`", parse_mode="Markdown")
        return

    user_id = get_user_id(msg)
    async with httpx.AsyncClient(base_url=settings.API_BASE_URL, timeout=10) as c:
        r = await c.post(f"/users/{user_id}/withdraw", json={"amount": amount, "dest": dest})
        if r.status_code >= 400:
            await msg.answer(f"Ошибка: {r.text}")
            return
        data = r.json()

    await msg.answer(f"Заявка на вывод создана: #{data['id']} (статус: {data['status']}). После модерации будет выплата.")

@router.message(F.text == "FAQ")
async def faq(msg: Message):
    await msg.answer("FAQ: Напишите в поддержку, мы поможем.")