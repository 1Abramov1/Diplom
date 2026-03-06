from app.core.event_loop import configure_event_loop

configure_event_loop()  # <-- Вызываем ДО создания приложения

from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Дипломный проект: сервис покупок для авторизованных пользователей",
    version=settings.VERSION
)

@app.get("/")
async def root():
    return {
        "message": "Сервис покупок работает!",
        "database": "PostgreSQL",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}