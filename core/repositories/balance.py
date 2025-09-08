from sqlalchemy.orm import Session
from sqlalchemy import and_
from core.models.user import User
from core.models.transaction import Transaction, TransactionType, TransactionStatus
from core.models.withdraw_request import WithdrawRequest, WithdrawStatus
from core.config import settings
from datetime import datetime, timedelta
from typing import Optional, List


class BalanceRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID"""
        return self.db.query(User).filter(User.telegram_id == telegram_id).first()

    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> User:
        """Создать нового пользователя"""
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user_balance(self, user_id: int, amount: float) -> bool:
        """Обновить баланс пользователя"""
        user = self.db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            return False
        
        user.balance += amount
        self.db.commit()
        return True

    def create_transaction(self, user_id: int, amount: float, 
                          transaction_type, 
                          description: str = None) -> Transaction:
        """Создать транзакцию"""
        transaction = Transaction(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            description=description,
            status=TransactionStatus.PENDING
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    def complete_transaction(self, transaction_id: int) -> bool:
        """Завершить транзакцию"""
        transaction = self.db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not transaction:
            return False
        
        transaction.status = TransactionStatus.COMPLETED
        transaction.processed_at = datetime.utcnow()
        self.db.commit()
        return True

    def create_withdraw_request(self, user_id: int, amount: float, 
                               payment_method: str, payment_details: str) -> WithdrawRequest:
        """Создать заявку на вывод средств"""
        admin_fee = amount * (settings.admin_percentage / 100)
        final_amount = amount - admin_fee
        
        withdraw_request = WithdrawRequest(
            user_id=user_id,
            amount=amount,
            admin_fee=admin_fee,
            final_amount=final_amount,
            payment_method=payment_method,
            payment_details=payment_details
        )
        self.db.add(withdraw_request)
        self.db.commit()
        self.db.refresh(withdraw_request)
        return withdraw_request

    def get_pending_withdraw_requests(self) -> List[WithdrawRequest]:
        """Получить все ожидающие заявки на вывод"""
        return self.db.query(WithdrawRequest).filter(
            WithdrawRequest.status == WithdrawStatus.PENDING
        ).all()

    def update_withdraw_request_status(self, request_id: int, status: WithdrawStatus, 
                                     admin_notes: str = None, processed_by: int = None) -> bool:
        """Обновить статус заявки на вывод"""
        withdraw_request = self.db.query(WithdrawRequest).filter(
            WithdrawRequest.id == request_id
        ).first()
        
        if not withdraw_request:
            return False
        
        withdraw_request.status = status
        withdraw_request.admin_notes = admin_notes
        withdraw_request.processed_by = processed_by
        
        if status in [WithdrawStatus.APPROVED, WithdrawStatus.REJECTED]:
            withdraw_request.processed_at = datetime.utcnow()
        
        self.db.commit()
        return True

    def can_user_withdraw(self, user_id: int) -> bool:
        """Проверить, может ли пользователь вывести средства (учитывая задержку)"""
        # Проверяем, есть ли недавние депозиты
        delay_date = datetime.utcnow() - timedelta(days=settings.withdrawal_delay_days)
        
        recent_deposits = self.db.query(Transaction).filter(
            and_(
                Transaction.user_id == user_id,
                Transaction.transaction_type == TransactionType.DEPOSIT,
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.created_at > delay_date
            )
        ).first()
        
        return recent_deposits is None

    def get_user_transactions(self, user_id: int, limit: int = 10) -> List[Transaction]:
        """Получить транзакции пользователя"""
        return self.db.query(Transaction).filter(
            Transaction.user_id == user_id
        ).order_by(Transaction.created_at.desc()).limit(limit).all()

    def get_user_withdraw_requests(self, user_id: int) -> List[WithdrawRequest]:
        """Получить заявки на вывод пользователя"""
        return self.db.query(WithdrawRequest).filter(
            WithdrawRequest.user_id == user_id
        ).order_by(WithdrawRequest.created_at.desc()).all()
