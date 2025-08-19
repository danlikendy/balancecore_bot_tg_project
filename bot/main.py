import asyncio
import logging
from aiogram import Bot, Dispatcher
from core.config import settings
from bot.handlers.menu import router as menu_router

# Логи на уровне INFO
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("balancecore-bot")

dp = Dispatcher()
dp.include_router(menu_router)

async def main():
    bot = Bot(settings.BOT_TOKEN)
    me = await bot.get_me()
    logger.info("Bot started as @%s (id=%s)", me.username, me.id)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())