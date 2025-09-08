from sqlalchemy import Column, BigInteger, Float, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.orm import relationship
from core.db import Base
from core.models.base import BaseModel
import enum


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    WAITING_FOR_CAPTURE = "waiting_for_capture"
    SUCCEEDED = "succeeded"
    CANCELED = "canceled"
    FAILED = "failed"


class PaymentMethod(str, enum.Enum):
    BANK_CARD = "bank_card"
    YOO_MONEY = "yoo_money"
    QIWI = "qiwi"
    WEBMONEY = "webmoney"
    ALFABANK = "alfabank"
    SBERBANK = "sberbank"


class Payment(Base, BaseModel):
    """Модель платежа"""
    __tablename__ = "payments"
    
    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)
    description = Column(String(500), nullable=True)
    payment_method = Column(Enum(PaymentMethod), nullable=True)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    
    # ЮKassa данные
    yookassa_payment_id = Column(String(255), nullable=True)
    yookassa_confirmation_url = Column(String(500), nullable=True)
    yookassa_status = Column(String(50), nullable=True)
    
    # Результат платежа
    is_paid = Column(Boolean, default=False, nullable=False)
    paid_at = Column(DateTime, nullable=True)
    
    # Связь с пользователем
    user = relationship("User", backref="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status={self.status})>"
