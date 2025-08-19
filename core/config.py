from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_BASE_URL: str = "http://api:8000"
    DATABASE_URL: str = "postgresql+psycopg2://app:app@db:5432/app"
    REDIS_URL: str = "redis://redis:6379/0"
    ADMIN_TOKEN: str

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )

settings = Settings()  # pyright: ignore[reportCallIssue]