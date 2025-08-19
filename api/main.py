# api/main.py
import logging
from fastapi import FastAPI, Depends, HTTPException, Header, Query
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session

from core.db import SessionLocal
from core.config import settings
from core.schemas.public import BalanceOut, Tariff as TariffSchema
from core.repositories.balance import get_balance, get_or_create_user
from core.models.withdraw_request import WithdrawRequest
from core.models.tariff import Tariff
from pydantic import BaseModel, Field

app = FastAPI(
    title="BalanceCore API",
    description="Core API для BalanceCore",
    version="1.0.0",
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("balancecore-api")

# CORS (в проде ограничить доменами)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- DB session ----
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---- System ----
@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

@app.get("/", tags=["system"])
def index():
    return {"service": "balancecore-api", "ok": True}

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})

# ---- Tariffs ----
@app.get("/tariffs", response_model=list[TariffSchema], tags=["tariffs"])
def list_tariffs(db: Session = Depends(get_db)):
    items = db.query(Tariff).all()
    return [TariffSchema(code=t.code, name=t.name, min_amount=t.min_amount) for t in items]

# ---- Balance ----
@app.get("/users/{user_id}/balance", response_model=BalanceOut, tags=["balance"])
def user_balance(user_id: int, db: Session = Depends(get_db)):
    get_or_create_user(db, user_id)
    return BalanceOut(user_id=user_id, balance=get_balance(db, user_id))

# ---- Withdraw (user) ----
class WithdrawIn(BaseModel):
    amount: float = Field(gt=0)
    dest: str = Field(min_length=3, max_length=128)

@app.post("/users/{user_id}/withdraw", tags=["withdraw"])
def request_withdraw(user_id: int, data: WithdrawIn, db: Session = Depends(get_db)):
    wr = WithdrawRequest(user_id=user_id, amount=data.amount, dest=data.dest, status="pending")
    db.add(wr)
    db.commit()
    db.refresh(wr)
    logger.info("withdraw.create user=%s id=%s amount=%.2f", user_id, wr.id, data.amount)
    return {"id": wr.id, "status": wr.status}

# ---- Admin moderation ----
def check_admin(x_admin_token: str | None = Header(default=None)):
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/admin/withdraws", tags=["admin"])
def admin_list_withdraws(
    status: str = Query(default="pending"),
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    q = (
        db.query(WithdrawRequest)
        .filter(WithdrawRequest.status == status)
        .order_by(WithdrawRequest.id.desc())
    )
    return [
        {
            "id": i.id,
            "user_id": i.user_id,
            "amount": float(i.amount),
            "dest": i.dest,
            "status": i.status,
        }
        for i in q.all()
    ]

@app.post("/admin/withdraws/{wr_id}/approve", tags=["admin"])
def admin_approve_withdraw(
    wr_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    wr = db.get(WithdrawRequest, wr_id)
    if not wr:
        raise HTTPException(404, "Not found")
    if wr.status != "pending":
        raise HTTPException(400, "Already processed")

    wr.status = "approved"

    # Списание: положительная сумма + kind='debit' (знак учитывается в расчёте баланса)
    from core.models.transaction import Transaction
    db.add(
        Transaction(
            user_id=wr.user_id,
            kind="debit",
            amount=float(wr.amount),
        )
    )

    db.commit()
    logger.info("withdraw.approve id=%s user=%s", wr.id, wr.user_id)
    return {"ok": True}

@app.post("/admin/withdraws/{wr_id}/reject", tags=["admin"])
def admin_reject_withdraw(
    wr_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(check_admin),
):
    wr = db.get(WithdrawRequest, wr_id)
    if not wr:
        raise HTTPException(404, "Not found")
    if wr.status != "pending":
        raise HTTPException(400, "Already processed")

    wr.status = "rejected"
    db.commit()
    logger.info("withdraw.reject id=%s user=%s", wr.id, wr.user_id)
    return {"ok": True}
