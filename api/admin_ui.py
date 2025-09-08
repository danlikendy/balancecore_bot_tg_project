from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from core.db import get_db
from core.repositories.balance import BalanceRepository
from core.models.withdraw_request import WithdrawRequest, WithdrawStatus
from core.models.user import User
from core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="api/templates")


def verify_admin(admin_telegram_id: int) -> bool:
    """Проверка прав администратора"""
    return admin_telegram_id == settings.admin_user_id


@router.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    """Главная страница админ-панели"""
    repo = BalanceRepository(db)
    
    # Получаем статистику
    pending_requests = repo.get_pending_withdraw_requests()
    
    context = {
        "request": request,
        "pending_count": len(pending_requests),
        "admin_percentage": settings.admin_percentage,
        "min_withdrawal": settings.min_withdrawal_amount,
        "withdrawal_delay": settings.withdrawal_delay_days
    }
    
    return templates.TemplateResponse("admin_dashboard.html", context)


@router.get("/admin/withdraws", response_class=HTMLResponse)
async def admin_withdraws(
    request: Request,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Страница управления заявками на вывод"""
    repo = BalanceRepository(db)
    
    if status == "pending":
        requests = repo.get_pending_withdraw_requests()
    else:
        # Получаем все заявки (можно добавить пагинацию)
        requests = db.query(WithdrawRequest).order_by(
            WithdrawRequest.created_at.desc()
        ).limit(50).all()
    
    context = {
        "request": request,
        "withdraw_requests": requests,
        "current_status": status,
        "WithdrawStatus": WithdrawStatus
    }
    
    return templates.TemplateResponse("admin_withdraws.html", context)


@router.post("/admin/withdraws/{request_id}/process")
async def process_withdraw_request(
    request_id: int,
    status: str = Form(...),
    admin_notes: Optional[str] = Form(None),
    admin_telegram_id: int = Form(...),
    db: Session = Depends(get_db)
):
    """Обработка заявки на вывод"""
    # Проверяем права администратора
    if not verify_admin(admin_telegram_id):
        raise HTTPException(status_code=403, detail="Access denied")
    
    repo = BalanceRepository(db)
    
    # Получаем заявку
    withdraw_request = db.query(WithdrawRequest).filter(
        WithdrawRequest.id == request_id
    ).first()
    
    if not withdraw_request:
        raise HTTPException(status_code=404, detail="Withdraw request not found")
    
    # Обновляем статус
    try:
        new_status = WithdrawStatus(status)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    success = repo.update_withdraw_request_status(
        request_id=request_id,
        status=new_status,
        admin_notes=admin_notes,
        processed_by=admin_telegram_id
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update withdraw request")
    
    # Если заявка одобрена, списываем средства с баланса
    if new_status == WithdrawStatus.APPROVED:
        # Создаем транзакцию на списание
        from core.models.transaction import TransactionType
        transaction = repo.create_transaction(
            user_id=withdraw_request.user_id,
            amount=-withdraw_request.amount,
            transaction_type=TransactionType.WITHDRAWAL,
            description=f"Withdrawal approved. Admin fee: {withdraw_request.admin_fee}"
        )
        
        # Обновляем баланс
        repo.update_user_balance(withdraw_request.user_id, -withdraw_request.amount)
        repo.complete_transaction(transaction.id)
    
    return RedirectResponse(url="/admin/withdraws", status_code=303)


@router.get("/admin/users", response_class=HTMLResponse)
async def admin_users(request: Request, db: Session = Depends(get_db)):
    """Страница управления пользователями"""
    # Получаем всех пользователей (можно добавить пагинацию)
    users = db.query(User).order_by(User.created_at.desc()).limit(100).all()
    
    context = {
        "request": request,
        "users": users
    }
    
    return templates.TemplateResponse("admin_users.html", context)
