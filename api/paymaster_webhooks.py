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

router = APIRouter(prefix="/paymaster", tags=["PayMaster Webhooks"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@router.post("/webhook")
async def paymaster_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Обработка входящих уведомлений от PayMaster о статусе платежа.
    """
    try:
        # Получаем данные из запроса
        form_data = await request.form()
        logging.info(f"Received PayMaster webhook: {dict(form_data)}")
        
        # Извлекаем основные параметры
        order_id = form_data.get("LMI_PAYMENT_NO")
        status = form_data.get("LMI_PAYMENT_STATUS")
        amount = form_data.get("LMI_PAYMENT_AMOUNT")
        user_id = form_data.get("LMI_CUSTOM_FIELD_1")
        
        if not order_id or not status:
            logging.warning("PayMaster webhook: Missing required fields")
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        # Находим платеж в базе данных
        payment = db.query(Payment).filter(Payment.yookassa_payment_id == order_id).first()
        if not payment:
            logging.warning(f"PayMaster webhook: Payment with orderId {order_id} not found")
            raise HTTPException(status_code=404, detail="Payment not found")
        
        # Обрабатываем статус платежа
        if status == "PAYED":
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
                
                logging.info(f"PayMaster webhook: Payment {order_id} succeeded. User {payment.user_id}, Deposit {deposit.id}")
        
        elif status in ["CANCELED", "AUTH_FAIL", "DEADLINE_EXPIRED"]:
            if payment.status not in [PaymentStatus.CANCELED, PaymentStatus.FAILED]:
                payment.status = PaymentStatus.FAILED
                db.add(payment)
                db.commit()
                db.refresh(payment)
                logging.warning(f"PayMaster webhook: Payment {order_id} failed/canceled. Status: {status}")
        
        else:
            logging.info(f"PayMaster webhook: Payment {order_id} status {status} (pending/unknown)")
        
        return Response(status_code=200)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing PayMaster webhook: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {e}")


@router.get("/webhook")
async def paymaster_webhook_get(request: Request, db: Session = Depends(get_db)):
    """
    Обработка GET запросов от PayMaster (для проверки webhook).
    """
    return {"status": "ok", "message": "PayMaster webhook is working"}
