from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database - используем psycopg (бинарная версия, не требует компиляции)
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres@localhost:5432/diploma_shop"

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