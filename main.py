from fastapi import FastAPI
from app.core.config import settings
from app.api.v1.endpoints import auth, users, products


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Дипломный проект: сервис покупок для авторизованных пользователей",
    version=settings.VERSION
)

# Подключаем роутеры
app.include_router(auth.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(products.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "Сервис покупок работает!",
        "database": "SQLite",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}