from sqlalchemy.orm import Session
from core.models.deposit import Deposit
from core.models.user import User
from core.models.transaction import Transaction, TransactionType, TransactionStatus
from datetime import datetime, timedelta
from typing import List
import logging

logger = logging.getLogger(__name__)


class InterestService:
    """Сервис для начисления процентов по депозитам"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_daily_interest(self) -> dict:
        """Рассчитать и начислить проценты за день"""
        result = {
            "processed_deposits": 0,
            "total_interest": 0.0,
            "errors": []
        }
        
        try:
            # Получаем все активные депозиты
            active_deposits = self.db.query(Deposit).filter(
                Deposit.is_active == True
            ).all()
            
            for deposit in active_deposits:
                try:
                    # Рассчитываем проценты
                    interest = deposit.calculate_interest()
                    
                    if interest > 0:
                        # Применяем проценты
                        deposit.apply_interest()
                        
                        # Создаем транзакцию для начисления процентов
                        transaction = Transaction(
                            user_id=deposit.user_id,
                            amount=interest,
                            transaction_type=TransactionType.INTEREST,
                            description=f"Начисление процентов по депозиту #{deposit.id}",
                            status=TransactionStatus.COMPLETED,
                            processed_at=datetime.utcnow()
                        )
                        self.db.add(transaction)
                        
                        # Обновляем баланс пользователя
                        user = self.db.query(User).filter(
                            User.telegram_id == deposit.user_id
                        ).first()
                        if user:
                            user.balance += interest
                        
                        result["processed_deposits"] += 1
                        result["total_interest"] += interest
                        
                        logger.info(f"Начислены проценты {interest:.2f} руб. по депозиту {deposit.id}")
                
                except Exception as e:
                    error_msg = f"Ошибка при начислении процентов по депозиту {deposit.id}: {str(e)}"
                    logger.error(error_msg)
                    result["errors"].append(error_msg)
            
            # Сохраняем изменения
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка при расчете процентов: {str(e)}")
            result["errors"].append(f"Общая ошибка: {str(e)}")
            self.db.rollback()
        
        return result
    
    def create_deposit(self, user_id: int, amount: float, daily_percentage: float = 1.0) -> Deposit:
        """Создать новый депозит"""
        deposit = Deposit(
            user_id=user_id,
            amount=amount,
            current_amount=amount,
            daily_percentage=daily_percentage,
            last_interest_date=datetime.utcnow()
        )
        
        self.db.add(deposit)
        self.db.commit()
        self.db.refresh(deposit)
        
        return deposit
    
    def close_deposit(self, deposit_id: int) -> bool:
        """Закрыть депозит и перевести средства на баланс"""
        try:
            deposit = self.db.query(Deposit).filter(
                Deposit.id == deposit_id,
                Deposit.is_active == True
            ).first()
            
            if not deposit:
                return False
            
            # Применяем последние проценты
            final_interest = deposit.apply_interest()
            
            # Закрываем депозит
            deposit.close_deposit()
            
            # Переводим средства на баланс пользователя
            user = self.db.query(User).filter(
                User.telegram_id == deposit.user_id
            ).first()
            
            if user:
                user.balance += deposit.current_amount
                
                # Создаем транзакцию
                transaction = Transaction(
                    user_id=deposit.user_id,
                    amount=deposit.current_amount,
                    transaction_type=TransactionType.WITHDRAWAL,
                    description=f"Закрытие депозита #{deposit.id}",
                    status=TransactionStatus.COMPLETED,
                    processed_at=datetime.utcnow()
                )
                self.db.add(transaction)
            
            self.db.commit()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка при закрытии депозита {deposit_id}: {str(e)}")
            self.db.rollback()
            return False
    
    def get_user_deposits(self, user_id: int) -> List[Deposit]:
        """Получить депозиты пользователя"""
        return self.db.query(Deposit).filter(
            Deposit.user_id == user_id
        ).order_by(Deposit.created_at.desc()).all()
    
    def get_active_deposits(self) -> List[Deposit]:
        """Получить все активные депозиты"""
        return self.db.query(Deposit).filter(
            Deposit.is_active == True
        ).all()
