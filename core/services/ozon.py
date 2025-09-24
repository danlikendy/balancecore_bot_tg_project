import hashlib
import requests
import json
from typing import Dict, Any
from core.config import Settings
from core.models.payment import PaymentStatus, PaymentMethod
from datetime import datetime
import uuid


class OzonPayService:
    """Сервис для работы с Ozon Pay API"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client_id = settings.ozon_client_id
        self.client_secret = settings.ozon_client_secret
        self.api_url = settings.ozon_api_url
        self.test_mode = settings.ozon_test_mode
        self.return_url = f"{settings.api_host}/ozon/webhook"
    
    def _generate_signature(self, params: Dict[str, Any], method: str = "POST") -> str:
        """Генерирует подпись для запроса Ozon Pay"""
        # Сортируем параметры по алфавиту
        sorted_params = sorted(f"{k}={v}" for k, v in params.items() if v is not None)
        string_to_sign = f"{method}&{'&'.join(sorted_params)}&{self.client_secret}"
        return hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
    
    def _get_access_token(self) -> str:
        """Получает access token для Ozon Pay API"""
        try:
            auth_data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "grant_type": "client_credentials"
            }
            
            response = requests.post(
                f"{self.api_url}/oauth/token",
                data=auth_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("access_token", "")
            
        except Exception as e:
            raise Exception(f"Failed to get Ozon access token: {e}")
    
    def create_payment(self, amount: float, description: str, user_id: int) -> Dict[str, Any]:
        """Создает платеж через Ozon Pay"""
        try:
            # Получаем access token
            access_token = self._get_access_token()
            
            # Генерируем уникальный ID заказа
            order_id = f"deposit_{user_id}_{int(datetime.now().timestamp())}"
            
            # Параметры для создания платежа
            payment_data = {
                "amount": {
                    "value": str(amount),
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": self.return_url
                },
                "description": description,
                "metadata": {
                    "user_id": str(user_id),
                    "order_id": order_id,
                    "type": "deposit"
                },
                "test": self.test_mode
            }
            
            # Отправляем запрос
            response = requests.post(
                f"{self.api_url}/v3/payments",
                json=payment_data,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            # Парсим ответ
            result = response.json()
            
            if result.get("status") == "pending":
                return {
                    "success": True,
                    "payment_id": result["id"],
                    "payment_url": result["confirmation"]["confirmation_url"],
                    "status": "pending"
                }
            else:
                return {
                    "success": False,
                    "error": f"Ozon Pay error: {result.get('description', 'Unknown error')}"
                }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Ozon Pay service error: {e}"}
    
    def check_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Проверяет статус платежа Ozon Pay"""
        try:
            # Получаем access token
            access_token = self._get_access_token()
            
            # Отправляем запрос
            response = requests.get(
                f"{self.api_url}/v3/payments/{payment_id}",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                },
                timeout=30
            )
            response.raise_for_status()
            
            # Парсим ответ
            result = response.json()
            
            # Маппинг статусов Ozon Pay
            status_map = {
                "pending": PaymentStatus.PENDING,
                "waiting_for_capture": PaymentStatus.PENDING,
                "succeeded": PaymentStatus.SUCCEEDED,
                "canceled": PaymentStatus.CANCELED,
                "failed": PaymentStatus.FAILED,
            }
            
            current_status = status_map.get(result.get("status"), PaymentStatus.PENDING)
            
            return {
                "success": True,
                "status": current_status,
                "amount": float(result.get("amount", {}).get("value", 0)),
                "raw_response": result
            }
                
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"HTTP request failed: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Ozon Pay status check error: {e}"}
    
    def get_payment_methods(self) -> Dict[str, Any]:
        """Получает доступные способы оплаты Ozon Pay"""
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
                {"id": "ozon_card", "name": "Ozon Карта", "icon": "🟠"},
                {"id": "ozon_bonus", "name": "Ozon Бонусы", "icon": "🎁"},
            ]
        }

