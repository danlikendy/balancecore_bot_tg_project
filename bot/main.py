import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage
from aiogram.fsm.storage.memory import MemoryStorage
import redis.asyncio as redis

from core.config import settings
from bot.handlers import menu, deposit, withdraw
from bot.middlewares.database import DatabaseMiddleware

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Основная функция запуска бота"""
    
    # Инициализация бота
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # Инициализация Redis для FSM
    try:
        redis_client = redis.from_url(settings.redis_url)
        storage = RedisStorage(redis=redis_client)
    except Exception as e:
        logger.warning(f"Redis недоступен, используем MemoryStorage: {e}")
        storage = MemoryStorage()
    
    # Инициализация диспетчера
    dp = Dispatcher(storage=storage)
    
    # Подключение middleware
    dp.message.middleware(DatabaseMiddleware())
    dp.callback_query.middleware(DatabaseMiddleware())
    
    # Регистрация роутеров
    dp.include_router(menu.router)
    dp.include_router(deposit.router)
    dp.include_router(withdraw.router)
    
    # Запуск бота
    try:
        logger.info("Запуск бота...")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
