from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database - SQLite!
    DATABASE_URL: str = "sqlite+aiosqlite:///./shop.db"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # App
    PROJECT_NAME: str = "Сервис покупок"
    VERSION: str = "1.0.0"

    class Config:
        env_file = ".env"


settings = Settings()