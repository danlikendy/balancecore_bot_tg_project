# api/main.py
import os
import logging
from fastapi import FastAPI, Depends, HTTPException, Header, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import (
    JSONResponse, FileResponse, PlainTextResponse, HTMLResponse, Response, RedirectResponse
)
from starlette.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from core.db import SessionLocal
from core.config import settings
from core.schemas.public import BalanceOut, Tariff as TariffSchema
from core.repositories.balance import get_balance, get_or_create_user
from core.models.withdraw_request import WithdrawRequest
from core.models.tariff import Tariff
from api.admin_ui import router as admin_ui_router  # оставим, если нет дублирующих путей
from fastapi.templating import Jinja2Templates

# --- Templates/Static ---
TEMPLATES_DIR = "api/templates"
STATIC_DIR = "api/static"
templates = Jinja2Templates(directory=TEMPLATES_DIR)

app = FastAPI(
    title="BalanceCore API",
    description="Core API для BalanceCore",
    version="1.0.2",
)

# монтируем статику только если папка существует
if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# дополнительный роутер (убедись, что пути не конфликтуют)
app.include_router(admin_ui_router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("balancecore-api")

# --- CORS ---
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

# ---- System / Ops ----
@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

@app.get("/", tags=["system"])
def index():
    return {"service": "balancecore-api", "ok": True}

# robots.txt (GET + HEAD)
def _robots_text() -> str:
    path = os.path.join(STATIC_DIR, "robots.txt")
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return "User-agent: *\nDisallow:\n"

@app.get("/robots.txt", response_class=PlainTextResponse, tags=["system"])
def robots_get():
    return _robots_text()

@app.head("/robots.txt", tags=["system"])
def robots_head():
    # HEAD должен вернуть только заголовки и длину, без тела
    content = _robots_text().encode("utf-8")
    return Response(status_code=200, media_type="text/plain; charset=utf-8", headers={"Content-Length": str(len(content))})

# favicon.ico (GET + HEAD)
@app.get("/favicon.ico", tags=["system"])
def favicon_get():
    path = os.path.join(STATIC_DIR, "favicon.ico")
    if os.path.isfile(path):
        return FileResponse(path, media_type="image/x-icon")
    # пустой ответ-иконка, чтобы не было 404
    return Response(content=b"", media_type="image/x-icon")

@app.head("/favicon.ico", tags=["system"])
def favicon_head():
    return Response(status_code=200, media_type="image/x-icon", headers={"Content-Length": "0"})

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
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

# ---- Admin JSON API (защита заголовком) ----
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

# ===== Admin UI (HTML) =====
# удобный редирект
@app.get("/admin", tags=["admin-ui"])
def admin_root_redirect():
    return RedirectResponse(url="/admin/ui/withdraws")

@app.get("/admin/ui/login", response_class=HTMLResponse, tags=["admin-ui"])
def admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/admin/ui/withdraws", response_class=HTMLResponse, tags=["admin-ui"])
def admin_withdraws_page(
    request: Request,
    status: str = "pending",
    db: Session = Depends(get_db),
):
    q = (
        db.query(WithdrawRequest)
        .filter(WithdrawRequest.status == status)
        .order_by(WithdrawRequest.id.desc())
    )
    withdraws = [
        {"id": i.id, "user_id": i.user_id, "amount": float(i.amount), "dest": i.dest, "status": i.status}
        for i in q.all()
    ]
    # ты создал шаблон 'admin_withdraws.html' и ждёшь переменную 'withdraws' — отдаём именно так
    return templates.TemplateResponse(
        "admin_withdraws.html",
        {"request": request, "status": status, "withdraws": withdraws},
    )