from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Bot Configuration
    bot_token: str
    admin_user_id: int
    
    # Database Configuration
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    
    # API Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str
    
    # Withdrawal Settings
    min_withdrawal_amount: int = 100
    admin_percentage: int = 5
    withdrawal_delay_days: int = 7
    
    # YooKassa Settings
    yookassa_shop_id: str = ""
    yookassa_secret_key: str = ""
    yookassa_test_mode: bool = True
    
    # PayMaster Settings
    paymaster_merchant_id: str = ""
    paymaster_secret_key: str = ""
    paymaster_api_url: str = "https://paymaster.ru"
    paymaster_test_mode: bool = True
    
    # Ozon Pay Settings
    ozon_client_id: str = ""
    ozon_client_secret: str = ""
    ozon_api_url: str = "https://api.ozon.ru"
    ozon_test_mode: bool = True
    
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
