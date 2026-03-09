import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

# Добавляем путь к проекту в sys.path (ИСПРАВЛЕНО!)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Теперь импортируем из корня проекта
from main import app
from app.core.database import Base, get_db
from app.core.security import get_password_hash
from app.models.user import User as UserModel
from app.models.product import Product as ProductModel
from app.models.cart import Cart as CartModel
from app.models.cart import CartItem as CartItemModel

pytestmark = pytest.mark.asyncio

# Тестовая база данных (SQLite in-memory)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Создание event loop для тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture()
async def engine():
    """Создание тестового движка БД"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Создание тестовой сессии БД"""
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session) -> AsyncGenerator[AsyncClient, None]:
    """Тестовый клиент FastAPI"""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ----- Фикстуры пользователей -----


@pytest.fixture
async def test_user(db_session) -> UserModel:
    """Создание тестового пользователя (с email)"""
    user = UserModel(
        email="test@example.com",
        full_name="Test User",
        hashed_password=get_password_hash("Testpass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_user_with_phone(db_session) -> UserModel:
    """Создание тестового пользователя с телефоном (без email)"""
    user = UserModel(
        phone="+79991234567",
        full_name="Phone User",
        hashed_password=get_password_hash("Testpass123!"),
        is_active=True,
        is_superuser=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_admin(db_session) -> UserModel:
    """Создание тестового админа"""
    admin = UserModel(
        email="admin@example.com",
        full_name="Admin User",
        hashed_password=get_password_hash("Admin123!"),
        is_active=True,
        is_superuser=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


# ----- Фикстуры товаров -----


@pytest.fixture
async def test_product(db_session) -> ProductModel:
    """Создание тестового товара"""
    product = ProductModel(
        name="Тестовый товар",
        description="Описание тестового товара",
        price=100.50,
        quantity=10,
        is_available=True,
    )
    db_session.add(product)
    await db_session.commit()
    await db_session.refresh(product)
    return product


# ----- Фикстуры корзины -----


@pytest.fixture
async def test_cart(db_session, test_user) -> CartModel:
    """Создание тестовой корзины"""
    cart = CartModel(user_id=test_user.id)
    db_session.add(cart)
    await db_session.commit()
    await db_session.refresh(cart)
    return cart


@pytest.fixture
async def test_cart_item(db_session, test_cart, test_product) -> CartItemModel:
    """Создание тестового элемента корзины"""
    item = CartItemModel(cart_id=test_cart.id, product_id=test_product.id, quantity=2)
    db_session.add(item)
    await db_session.commit()
    await db_session.refresh(item)
    return item


@pytest.fixture
async def test_cart_with_items(db_session, test_user, test_product) -> CartModel:
    """Создание корзины с товарами"""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    cart = CartModel(user_id=test_user.id)
    db_session.add(cart)
    await db_session.flush()

    item = CartItemModel(cart_id=cart.id, product_id=test_product.id, quantity=3)
    db_session.add(item)
    await db_session.commit()

    # Перезагружаем корзину с загруженными товарами
    result = await db_session.execute(
        select(CartModel)
        .where(CartModel.id == cart.id)
        .options(selectinload(CartModel.items).selectinload(CartItemModel.product))
    )
    cart_with_items = result.scalar_one()
    return cart_with_items


# ----- Фикстуры заголовков авторизации -----


@pytest.fixture
async def auth_headers(client, test_user):
    """Получение заголовков с токеном для обычного пользователя"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "Testpass123!"},
    )
    print(f"Login response status: {response.status_code}")
    print(f"Login response body: {response.text}")

    assert response.status_code == 200, f"Login failed: {response.text}"
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_headers(client, test_admin):
    """Получение заголовков с токеном для админа"""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "admin@example.com", "password": "Admin123!"},
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
