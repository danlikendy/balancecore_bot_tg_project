from sqlalchemy import Column, BigInteger, Float, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from core.db import Base
from core.models.base import BaseModel
import enum


class WithdrawStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"


class WithdrawRequest(Base, BaseModel):
    """Модель заявки на вывод средств"""
    __tablename__ = "withdraw_requests"
    
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)
    admin_fee = Column(Float, nullable=False)
    final_amount = Column(Float, nullable=False)  # Сумма к выплате после вычета комиссии
    status = Column(Enum(WithdrawStatus), default=WithdrawStatus.PENDING, nullable=False)
    payment_method = Column(String(100), nullable=False)  # Способ вывода (карта, кошелек и т.д.)
    payment_details = Column(String(500), nullable=False)  # Реквизиты для вывода
    admin_notes = Column(String(1000), nullable=True)  # Заметки администратора
    processed_at = Column(DateTime, nullable=True)
    processed_by = Column(BigInteger, nullable=True)  # ID администратора, обработавшего заявку
    
    # Связь с пользователем
    user = relationship("User", backref="withdraw_requests")
    
    def __repr__(self):
        return f"<WithdrawRequest(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
