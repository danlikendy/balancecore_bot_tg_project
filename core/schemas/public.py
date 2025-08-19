from pydantic import BaseModel

class BalanceOut(BaseModel):
    user_id: int
    balance: float

class Tariff(BaseModel):
    code: str
    name: str
    min_amount: int
