from sqlalchemy import Column, Integer, BigInteger, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from core.db import Base
from core.models.base import BaseModel


class Deposit(Base, BaseModel):
    """Модель депозита с процентами"""
    __tablename__ = "deposits"

    user_id = Column(BigInteger, ForeignKey("users.telegram_id"), nullable=False)
    amount = Column(Float, nullable=False)  # Изначальная сумма депозита
    current_amount = Column(Float, nullable=False)  # Текущая сумма с процентами
    daily_percentage = Column(Float, nullable=False, default=1.0)  # Процент в день
    last_interest_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, nullable=False)
    closed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="deposits")

    def calculate_interest(self) -> float:
        """Рассчитать проценты с последнего начисления"""
        if not self.is_active:
            return 0.0
        
        now = datetime.utcnow()
        days_passed = (now - self.last_interest_date).days
        
        if days_passed <= 0:
            return 0.0
        
        # Рассчитываем проценты за каждый день
        interest = 0.0
        current_amount = self.current_amount
        
        for day in range(days_passed):
            daily_interest = current_amount * (self.daily_percentage / 100)
            interest += daily_interest
            current_amount += daily_interest
        
        return interest

    def apply_interest(self) -> float:
        """Применить начисленные проценты"""
        interest = self.calculate_interest()
        if interest > 0:
            self.current_amount += interest
            self.last_interest_date = datetime.utcnow()
        return interest

    def close_deposit(self):
        """Закрыть депозит"""
        self.is_active = False
        self.closed_at = datetime.utcnow()
        # Применяем последние проценты перед закрытием
        self.apply_interest()

    def __repr__(self):
        return f"<Deposit(id={self.id}, user_id={self.user_id}, amount={self.amount}, current={self.current_amount})>"
