from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer
from core.models.base import Base

class Tariff(Base):
    __tablename__ = "tariffs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)  # PK
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    min_amount: Mapped[int] = mapped_column(Integer, nullable=False)