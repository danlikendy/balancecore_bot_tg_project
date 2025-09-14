from sqlalchemy import Column, BigInteger, Float, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from core.db import Base
from core.models.base import BaseModel
import enum


class TransactionType(str, enum.Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTEREST = "interest"
    ADMIN_BONUS = "admin_bonus"
    ADMIN_PENALTY = "admin_penalty"


class TransactionStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Transaction(Base, BaseModel):
    """Модель транзакции"""
    __tablename__ = "transactions"
    
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)
    transaction_type = Column(Enum(TransactionType), nullable=False)
    status = Column(Enum(TransactionStatus), default=TransactionStatus.PENDING, nullable=False)
    description = Column(String(500), nullable=True)
    admin_fee = Column(Float, default=0.0, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    
    # Связь с пользователем
    user = relationship("User", backref="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, user_id={self.user_id}, amount={self.amount}, type={self.transaction_type})>"
