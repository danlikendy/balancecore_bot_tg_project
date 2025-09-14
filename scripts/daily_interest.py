#!/usr/bin/env python3
"""
Скрипт для ежедневного начисления процентов по депозитам
Запускается по расписанию (например, через cron)
"""

import sys
import os
import logging
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db import SessionLocal
from core.services.interest import InterestService

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/daily_interest.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Основная функция для начисления процентов"""
    logger.info("Начинаем начисление процентов за день")
    
    db = SessionLocal()
    try:
        interest_service = InterestService(db)
        
        # Рассчитываем и начисляем проценты
        result = interest_service.calculate_daily_interest()
        
        logger.info(f"Начисление завершено:")
        logger.info(f"- Обработано депозитов: {result['processed_deposits']}")
        logger.info(f"- Общая сумма процентов: {result['total_interest']:.2f} руб.")
        
        if result['errors']:
            logger.warning(f"Ошибки при начислении: {len(result['errors'])}")
            for error in result['errors']:
                logger.error(error)
        
        logger.info("Начисление процентов завершено успешно")
        
    except Exception as e:
        logger.error(f"Критическая ошибка при начислении процентов: {str(e)}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()
