import asyncio
from app.core.database import engine, Base
from app.models import user  # импортируем модели

async def init_db():
    """Создание всех таблиц в базе данных"""
    print("🔄 Создание таблиц...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Таблицы созданы!")

if __name__ == "__main__":
    asyncio.run(init_db())