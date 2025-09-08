from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from sqlalchemy.orm import Session

from core.db import SessionLocal
from core.repositories.balance import BalanceRepository
from core.config import settings


class DatabaseMiddleware(BaseMiddleware):
    """Middleware для работы с базой данных"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка middleware"""
        
        # Получаем сессию базы данных
        db = SessionLocal()
        try:
            # Добавляем репозиторий в данные
            data["db"] = db
            data["balance_repo"] = BalanceRepository(db)
            
            # Получаем или создаем пользователя
            user_id = event.from_user.id
            user = data["balance_repo"].get_user_by_telegram_id(user_id)
            
            if not user:
                user = data["balance_repo"].create_user(
                    telegram_id=user_id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name
                )
            
            data["user"] = user
            data["is_admin"] = user_id == settings.admin_user_id
            
            # Вызываем следующий обработчик
            return await handler(event, data)
            
        finally:
            db.close()
