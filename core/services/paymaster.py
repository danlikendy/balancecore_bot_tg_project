import hashlib
import requests
import json
from typing import Dict, Any
from core.config import Settings
from core.models.payment import PaymentStatus, PaymentMethod
from datetime import datetime


class PayMasterService:
    """Сервис для работы с PayMaster API"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.merchant_id = settings.paymaster_merchant_id
        self.secret_key = settings.paymaster_secret_key
        self.api_url = settings.paymaster_api_url
        self.test_mode = settings.paymaster_test_mode
        self.return_url = f"{settings.api_host}/paymaster/webhook"
    
    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """Генерирует подпись для запроса PayMaster"""
        # Сортируем параметры по алфавиту
        sorted_params = sorted(f"{k}={v}" for k, v in params.items() if v is not None)
        string_to_sign = "&".join(sorted_params) + self.secret_key
        return hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
    
    def create_payment(self, amount: float, description: str, user_id: int) -> Dict[str, Any]:
        """Создает платеж через PayMaster"""
        try:
            # Генерируем уникальный ID заказа
            order_id = f"deposit_{user_id}_{int(datetime.now().timestamp())}"
            
            # Параметры для создания платежа
            params = {
                "LMI_MERCHANT_ID": self.merchant_id,
                "LMI_PAYMENT_AMOUNT": str(amount),
                "LMI_CURRENCY": "RUB",
                "LMI_PAYMENT_DESCRIPTION": description,
                "LMI_PAYMENT_NO": order_id,
                "LMI_RETURN_URL": self.return_url,
                "LMI_FAIL_URL": self.return_url,
                "LMI_SUCCESS_URL": self.return_url,
                "LMI_PAYMENT_METHOD": "ALL",  # Все доступные способы оплаты
                "LMI_AUTO_LOCATION": "1",  # Автоматическое определение локации
                "LMI_PAYMENT_NOTIFICATION_URL": self.return_url,
                "LMI_SIM_MODE": "1" if self.test_mode else "0",  # Тестовый режим
                "LMI_PAYMENT_AMOUNT_DEFAULT": str(amount),
                "LMI_CUSTOM_FIELD_1": str(user_id),  # ID пользователя
                "LMI_CUSTOM_FIELD_2": "deposit",  # Тип операции
            }
            
            # Генерируем подпись
            signature = self._generate_signature(params)
            params["LMI_HASH"] = signature
            
            # URL для создания платежа
            payment_url = f"{self.api_url}/payment/rest/register.do"
            
            # Отправляем запрос
            response = requests.post(payment_url, data=params, timeout=30)
            response.raise_for_status()
            
            # Парсим ответ
            result = response.json()
            
            if result.get("errorCode") == "0":
                return {
                    "success": True,
                    "payment_id": result["orderId"],
                    "payment_url": result["formUrl"],
                    "qr_code": result.get("qrId"),
                    "status": "pending"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("errorMessage", "Unknown PayMaster error")
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"PayMaster service error: {e}"}
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверяет статус платежа PayMaster"""
        try:
            params = {
                "LMI_MERCHANT_ID": self.merchant_id,
                "LMI_PAYMENT_NO": payment_id,
            }
            
            # Генерируем подпись
            signature = self._generate_signature(params)
            params["LMI_HASH"] = signature
            
            # URL для проверки статуса
            status_url = f"{self.api_url}/payment/rest/getOrderStatusExtended.do"
            
            # Отправляем запрос
            response = requests.post(status_url, data=params, timeout=30)
            response.raise_for_status()
            
            # Парсим ответ
            result = response.json()
            
            if result.get("errorCode") == "0":
                # Маппинг статусов PayMaster
                status_map = {
                    "NEW": PaymentStatus.PENDING,
                    "FORM_SHOWED": PaymentStatus.PENDING,
                    "DEADLINE_EXPIRED": PaymentStatus.CANCELED,
                    "CANCELED": PaymentStatus.CANCELED,
                    "PREAUTHORIZING": PaymentStatus.PENDING,
                    "AUTHORIZING": PaymentStatus.PENDING,
                    "AUTH_FAIL": PaymentStatus.FAILED,
                    "AUTH_FAIL": PaymentStatus.FAILED,
                    "3DS_CHECKING": PaymentStatus.PENDING,
                    "3DS_CHECKED": PaymentStatus.PENDING,
                    "PAYED": PaymentStatus.SUCCEEDED,
                    "AUTHORIZED": PaymentStatus.SUCCEEDED,
                    "REVERSED": PaymentStatus.CANCELED,
                    "REFUNDED": PaymentStatus.CANCELED,
                    "PARTIAL_REFUNDED": PaymentStatus.SUCCEEDED,
                }
                
                current_status = status_map.get(result.get("orderStatus"), PaymentStatus.PENDING)
                
                return {
                    "success": True,
                    "status": current_status,
                    "amount": float(result.get("orderSum", 0)),
                    "raw_response": result
                }
            else:
                return {
                    "success": False,
                    "error": result.get("errorMessage", "Unknown PayMaster error")
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"PayMaster status check error: {e}"}
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Получает доступные способы оплаты PayMaster"""
        return {
            "success": True,
            "methods": [
                {"id": "bank_card", "name": "Банковская карта", "icon": "💳"},
                {"id": "yoomoney", "name": "ЮMoney", "icon": "💰"},
                {"id": "qiwi", "name": "QIWI Кошелек", "icon": "🟣"},
                {"id": "webmoney", "name": "WebMoney", "icon": "🟠"},
                {"id": "alfabank", "name": "Альфа-Клик", "icon": "🔵"},
                {"id": "sberbank", "name": "Сбербанк Онлайн", "icon": "🟢"},
                {"id": "tinkoff", "name": "Тинькофф", "icon": "🟡"},
                {"id": "vtb", "name": "ВТБ", "icon": "🔴"},
                {"id": "mts", "name": "МТС", "icon": "📱"},
                {"id": "beeline", "name": "Билайн", "icon": "🟡"},
                {"id": "megafon", "name": "МегаФон", "icon": "🟢"},
            ]
        }
