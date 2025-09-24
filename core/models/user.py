from sqlalchemy import Column, BigInteger, String, Float, Boolean
from sqlalchemy.orm import relationship
from core.db import Base
from core.models.base import BaseModel


class User(Base, BaseModel):
    """Модель пользователя"""
    __tablename__ = "users"
    
    telegram_id = Column(BigInteger, unique=True, index=True, nullable=False)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    balance = Column(Float, default=0.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Связи
    deposits = relationship("Deposit", back_populates="user")
    
    def get_total_deposits(self) -> float:
        """Получить общую сумму активных депозитов"""
        total = 0.0
        for deposit in self.deposits:
            if deposit.is_active:
                total += deposit.current_amount
        return total
    
    def get_total_interest_earned(self) -> float:
        """Получить общую сумму заработанных процентов"""
        total_interest = 0.0
        for deposit in self.deposits:
            if deposit.is_active:
                total_interest += deposit.current_amount - deposit.amount
        return total_interest
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, username={self.username}, balance={self.balance})>"
