from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List
import uvicorn

from core.db import get_db
from core.repositories.balance import BalanceRepository
from core.schemas.public import (
    UserResponse, TransactionResponse, WithdrawRequestResponse,
    WithdrawRequestCreate, WithdrawRequestUpdate, BalanceUpdate
)
from core.models.transaction import TransactionType, TransactionStatus
from core.models.withdraw_request import WithdrawRequest, WithdrawStatus
from core.config import settings
from api.admin_ui import router as admin_router
from api.paymaster_webhooks import router as paymaster_router
from api.ozon_webhooks import router as ozon_router

app = FastAPI(
    title="BalanceCore Bot API",
    description="API для управления балансом пользователей",
    version="1.0.0"
)

# Подключаем роутеры
app.include_router(admin_router)
app.include_router(paymaster_router)
app.include_router(ozon_router)

# Подключаем статические файлы и шаблоны
app.mount("/static", StaticFiles(directory="api/static"), name="static")
templates = Jinja2Templates(directory="api/templates")


@app.get("/")
async def root():
    return {"message": "BalanceCore Bot API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Пользователи
@app.get("/users/{telegram_id}", response_model=UserResponse)
async def get_user(telegram_id: int, db: Session = Depends(get_db)):
    """Получить информацию о пользователе"""
    repo = BalanceRepository(db)
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.post("/users", response_model=UserResponse)
async def create_user(
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None,
    db: Session = Depends(get_db)
):
    """Создать нового пользователя"""
    repo = BalanceRepository(db)
    user = repo.get_user_by_telegram_id(telegram_id)
    if user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user = repo.create_user(telegram_id, username, first_name, last_name)
    return user


# Баланс
@app.post("/balance/deposit")
async def deposit_balance(
    telegram_id: int,
    balance_update: BalanceUpdate,
    db: Session = Depends(get_db)
):
    """Пополнить баланс пользователя"""
    repo = BalanceRepository(db)
    
    # Получаем или создаем пользователя
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Создаем транзакцию
    transaction = repo.create_transaction(
        user_id=telegram_id,
        amount=balance_update.amount,
        transaction_type=TransactionType.DEPOSIT,
        description=balance_update.description
    )
    
    # Обновляем баланс
    success = repo.update_user_balance(telegram_id, balance_update.amount)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update balance")
    
    # Завершаем транзакцию
    repo.complete_transaction(transaction.id)
    
    return {"message": "Balance updated successfully", "transaction_id": transaction.id}


@app.get("/balance/{telegram_id}")
async def get_balance(telegram_id: int, db: Session = Depends(get_db)):
    """Получить баланс пользователя"""
    repo = BalanceRepository(db)
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"balance": user.balance, "user_id": telegram_id}


# Транзакции
@app.get("/transactions/{telegram_id}", response_model=List[TransactionResponse])
async def get_user_transactions(
    telegram_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Получить транзакции пользователя"""
    repo = BalanceRepository(db)
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    transactions = repo.get_user_transactions(telegram_id, limit)
    return transactions


# Заявки на вывод
@app.post("/withdraw/request", response_model=WithdrawRequestResponse)
async def create_withdraw_request(
    telegram_id: int,
    request: WithdrawRequestCreate,
    db: Session = Depends(get_db)
):
    """Создать заявку на вывод средств"""
    repo = BalanceRepository(db)
    
    # Проверяем пользователя
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Проверяем баланс
    if user.balance < request.amount:
        raise HTTPException(status_code=400, detail="Insufficient balance")
    
    # Проверяем минимальную сумму
    if request.amount < settings.min_withdrawal_amount:
        raise HTTPException(
            status_code=400, 
            detail=f"Minimum withdrawal amount is {settings.min_withdrawal_amount}"
        )
    
    # Проверяем, может ли пользователь вывести средства
    if not repo.can_user_withdraw(telegram_id):
        raise HTTPException(
            status_code=400,
            detail=f"Withdrawal is not available yet. Please wait {settings.withdrawal_delay_days} days after your last deposit."
        )
    
    # Создаем заявку
    withdraw_request = repo.create_withdraw_request(
        user_id=telegram_id,
        amount=request.amount,
        payment_method=request.payment_method,
        payment_details=request.payment_details
    )
    
    return withdraw_request


@app.get("/withdraw/requests/{telegram_id}", response_model=List[WithdrawRequestResponse])
async def get_user_withdraw_requests(
    telegram_id: int,
    db: Session = Depends(get_db)
):
    """Получить заявки на вывод пользователя"""
    repo = BalanceRepository(db)
    user = repo.get_user_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    requests = repo.get_user_withdraw_requests(telegram_id)
    return requests


# Админские функции
@app.get("/admin/withdraw/pending", response_model=List[WithdrawRequestResponse])
async def get_pending_withdraw_requests(db: Session = Depends(get_db)):
    """Получить все ожидающие заявки на вывод (только для админов)"""
    repo = BalanceRepository(db)
    requests = repo.get_pending_withdraw_requests()
    return requests


@app.post("/admin/withdraw/{request_id}/process")
async def process_withdraw_request(
    request_id: int,
    update: WithdrawRequestUpdate,
    admin_telegram_id: int,
    db: Session = Depends(get_db)
):
    """Обработать заявку на вывод (только для админов)"""
    repo = BalanceRepository(db)
    
    # Получаем заявку
    withdraw_request = db.query(WithdrawRequest).filter(
        WithdrawRequest.id == request_id
    ).first()
    
    if not withdraw_request:
        raise HTTPException(status_code=404, detail="Withdraw request not found")
    
    # Обновляем статус
    success = repo.update_withdraw_request_status(
        request_id=request_id,
        status=update.status,
        admin_notes=update.admin_notes,
        processed_by=admin_telegram_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update withdraw request")
    
    # Если заявка одобрена, списываем средства с баланса
    if update.status == WithdrawStatus.APPROVED:
        # Создаем транзакцию на списание
        transaction = repo.create_transaction(
            user_id=withdraw_request.user_id,
            amount=-withdraw_request.amount,  # Отрицательная сумма для списания
            transaction_type=TransactionType.WITHDRAWAL,
            description=f"Withdrawal approved. Admin fee: {withdraw_request.admin_fee}"
        )
        
        # Обновляем баланс
        repo.update_user_balance(withdraw_request.user_id, -withdraw_request.amount)
        repo.complete_transaction(transaction.id)
    
    return {"message": "Withdraw request processed successfully"}


if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )
