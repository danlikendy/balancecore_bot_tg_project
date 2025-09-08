import uuid
from typing import Optional, Dict, Any
from yookassa import Configuration, Payment

from core.config import settings


class YooKassaService:
    """Сервис для работы с ЮKassa"""
    
    def __init__(self):
        # Настройка ЮKassa
        Configuration.account_id = settings.yookassa_shop_id
        Configuration.secret_key = settings.yookassa_secret_key
    
    async def create_payment(
        self, 
        amount: float, 
        description: str, 
        user_id: int,
        return_url: str = None
    ) -> Dict[str, Any]:
        """Создать платеж в ЮKassa"""
        
        # Генерируем уникальный ID платежа
        payment_id = str(uuid.uuid4())
        
        # Создаем платеж
        payment = YooPayment.create({
            "amount": {
                "value": f"{amount:.2f}",
                "currency": Currency.RUB
            },
            "confirmation": {
                "type": ConfirmationType.REDIRECT,
                "return_url": return_url or f"https://t.me/balancecore_bot"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "payment_id": payment_id
            }
        })
        
        return {
            "payment_id": payment.id,
            "confirmation_url": payment.confirmation.confirmation_url,
            "status": payment.status,
            "amount": amount,
            "description": description
        }
    
    async def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверить статус платежа"""
        
        try:
            payment = Payment.find_one(payment_id)
            
            return {
                "payment_id": payment.id,
                "status": payment.status,
                "paid": payment.paid,
                "amount": float(payment.amount.value),
                "metadata": payment.metadata
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }
    
    async def get_payment_methods(self) -> list:
        """Получить доступные способы оплаты"""
        return [
            {
                "id": "bank_card",
                "name": "Банковская карта",
                "description": "Visa, MasterCard, МИР"
            },
            {
                "id": "yoo_money",
                "name": "ЮMoney",
                "description": "Электронный кошелек"
            },
            {
                "id": "qiwi",
                "name": "QIWI Кошелек",
                "description": "Пополнение через QIWI"
            },
            {
                "id": "webmoney",
                "name": "WebMoney",
                "description": "Электронные деньги"
            },
            {
                "id": "alfabank",
                "name": "Альфа-Клик",
                "description": "Интернет-банк Альфа-Банка"
            },
            {
                "id": "sberbank",
                "name": "Сбербанк Онлайн",
                "description": "Интернет-банк Сбербанка"
            }
        ]


# Создаем экземпляр сервиса
yookassa_service = YooKassaService()
