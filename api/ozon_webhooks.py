from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from core.db import get_db
from core.repositories.balance import BalanceRepository
from core.models.payment import Payment, PaymentStatus
from core.models.deposit import Deposit
from core.services.interest import InterestService
import logging
import json
from datetime import datetime

router = APIRouter(prefix="/ozon", tags=["Ozon Pay Webhooks"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@router.post("/webhook")
async def ozon_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Обработка входящих уведомлений от Ozon Pay о статусе платежа.
    """
    try:
        # Получаем данные из запроса
        body = await request.body()
        data = json.loads(body.decode('utf-8'))
        logging.info(f"Received Ozon Pay webhook: {data}")
        
        # Извлекаем основные параметры
        payment_id = data.get("object", {}).get("id")
        status = data.get("object", {}).get("status")
        amount = data.get("object", {}).get("amount", {}).get("value")
        user_id = data.get("object", {}).get("metadata", {}).get("user_id")
        
        if not payment_id or not status:
            logging.warning("Ozon Pay webhook: Missing required fields")
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Находим платеж в базе данных
        payment = db.query(Payment).filter(Payment.yookassa_payment_id == payment_id).first()
        if not payment:
            logging.warning(f"Ozon Pay webhook: Payment with id {payment_id} not found")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Обрабатываем статус платежа
        if status == "succeeded":
            if payment.status != PaymentStatus.SUCCEEDED:
                payment.status = PaymentStatus.SUCCEEDED
                payment.is_paid = True
                payment.paid_at = datetime.utcnow()
                db.add(payment)
                db.commit()
                db.refresh(payment)
                
                # Создаем депозит для пользователя
                interest_service = InterestService(db)
                deposit = interest_service.create_deposit(
                    user_id=payment.user_id,
                    amount=payment.amount,
                    daily_percentage=1.0  # 1% в день
                )
                
                logging.info(f"Ozon Pay webhook: Payment {payment_id} succeeded. User {payment.user_id}, Deposit {deposit.id}")
        
        elif status in ["canceled", "failed"]:
            if payment.status not in [PaymentStatus.CANCELED, PaymentStatus.FAILED]:
                payment.status = PaymentStatus.FAILED
                db.add(payment)
                db.commit()
                db.refresh(payment)
                logging.warning(f"Ozon Pay webhook: Payment {payment_id} failed/canceled. Status: {status}")
        
        else:
            logging.info(f"Ozon Pay webhook: Payment {payment_id} status {status} (pending/unknown)")
        
        return Response(status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing Ozon Pay webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/webhook")
async def ozon_webhook_get(request: Request, db: Session = Depends(get_db)):
    """
    Обработка GET запросов от Ozon Pay (для проверки webhook).
    """
    return {"status": "ok", "message": "Ozon Pay webhook is working"}

