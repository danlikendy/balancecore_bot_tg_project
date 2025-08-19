from sqlalchemy import BigInteger, String, Numeric, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column
from core.models.base import Base

class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    amount: Mapped[float] = mapped_column(Numeric(18, 2))
    dest: Mapped[str] = mapped_column(String(128))   # реквизиты/метод
    status: Mapped[str] = mapped_column(String(16), default="pending")  # pending|approved|rejected|paid
    created_at: Mapped[str] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
