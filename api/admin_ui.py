from fastapi import APIRouter, Depends, Request, HTTPException, Header, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from core.config import settings
from core.db import SessionLocal
from core.models.withdraw_request import WithdrawRequest
from core.repositories.balance import get_balance, get_or_create_user

router = APIRouter()
templates = Jinja2Templates(directory="api/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Защита только для POST-действий (браузер не шлёт заголовок сам)
def admin_guard(x_admin_token: str | None = Header(default=None)):
    if x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/admin", response_class=HTMLResponse)
def admin_root(request: Request):
    # Покажем простую страницу логина (кладёт токен в localStorage)
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/admin/withdraws", response_class=HTMLResponse)
def admin_withdraws(
    request: Request,
    status: str = Query(default="pending"),
    db: Session = Depends(get_db),
):
    # Страница рендерится без заголовка; кнопки внутри шлют токен через JS
    items = (
        db.query(WithdrawRequest)
        .filter(WithdrawRequest.status == status)
        .order_by(WithdrawRequest.id.desc())
        .all()
    )
    return templates.TemplateResponse(
        "withdraws.html",
        {"request": request, "items": items, "status": status},
    )


@router.post("/admin/withdraws/{wr_id}/approve")
def ui_approve(
    wr_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(admin_guard),  # <-- Действие защищено токеном
):
    from core.models.transaction import Transaction

    wr = db.get(WithdrawRequest, wr_id)
    if not wr:
        raise HTTPException(404, "Not found")
    if wr.status != "pending":
        raise HTTPException(400, "Already processed")

    wr.status = "approved"
    db.add(Transaction(user_id=wr.user_id, kind="debit", amount=-float(wr.amount)))
    db.commit()
    return JSONResponse({"ok": True})


@router.post("/admin/withdraws/{wr_id}/reject")
def ui_reject(
    wr_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(admin_guard),  # <-- Действие защищено токеном
):
    wr = db.get(WithdrawRequest, wr_id)
    if not wr:
        raise HTTPException(404, "Not found")
    if wr.status != "pending":
        raise HTTPException(400, "Already processed")

    wr.status = "rejected"
    db.commit()
    return JSONResponse({"ok": True})


@router.get("/admin/users", response_class=HTMLResponse)
def admin_users(
    request: Request,
    user_id: int | None = None,
    db: Session = Depends(get_db),
):
    # Страница открывается без токена; только просмотр/калькуляция
    balance = None
    if user_id is not None:
        get_or_create_user(db, user_id)
        balance = get_balance(db, user_id)
    return templates.TemplateResponse(
        "users.html",
        {"request": request, "user_id": user_id, "balance": balance},
    )