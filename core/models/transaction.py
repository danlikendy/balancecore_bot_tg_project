from sqlalchemy import BigInteger, String, Numeric, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from core.models.base import Base

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    kind: Mapped[str] = mapped_column(String(20))  # TOPUP|WITHDRAW|ADJUST
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())