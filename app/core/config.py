from pydantic_settings import BaseSettings
from pydantic import ConfigDict


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

    model_config = ConfigDict(from_attributes=True)


settings = Settings()
