from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from core.models.transaction import TransactionType, TransactionStatus
from core.models.withdraw_request import WithdrawStatus


class UserBase(BaseModel):
    telegram_id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    balance: float = 0.0


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TransactionBase(BaseModel):
    amount: float
    transaction_type: TransactionType
    description: Optional[str] = None


class TransactionCreate(TransactionBase):
    user_id: int


class TransactionResponse(TransactionBase):
    id: int
    user_id: int
    status: TransactionStatus
    admin_fee: float
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WithdrawRequestBase(BaseModel):
    amount: float
    payment_method: str
    payment_details: str


class WithdrawRequestCreate(WithdrawRequestBase):
    pass


class WithdrawRequestResponse(WithdrawRequestBase):
    id: int
    user_id: int
    admin_fee: float
    final_amount: float
    status: WithdrawStatus
    admin_notes: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    processed_by: Optional[int] = None

    class Config:
        from_attributes = True


class WithdrawRequestUpdate(BaseModel):
    status: WithdrawStatus
    admin_notes: Optional[str] = None


class BalanceUpdate(BaseModel):
    amount: float
    description: Optional[str] = None
