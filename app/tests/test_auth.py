import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAuth:
    """Тесты авторизации"""

    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "newpass123"
            }
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Регистрация с существующим email"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "username": "another",
                "password": "pass123"
            }
        )
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    async def test_register_duplicate_username(self, client: AsyncClient, test_user):
        """Регистрация с существующим username"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "another@example.com",
                "username": "testuser",
                "password": "pass123"
            }
        )
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    async def test_login_success(self, client: AsyncClient, test_user):
        """Успешный логин"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "test@example.com"

    async def test_login_wrong_password(self, client: AsyncClient, test_user):
        """Логин с неверным паролем"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "test@example.com",
                "password": "wrongpass"
            }
        )
        assert response.status_code == 401
        assert "Неверный" in response.json()["detail"]

    async def test_login_wrong_username(self, client: AsyncClient):
        """Логин с неверным username"""
        response = await client.post(
            "/api/v1/auth/login",
            data={
                "username": "nonexistent@example.com",
                "password": "testpass123"
            }
        )
        assert response.status_code == 401
        assert "Неверный" in response.json()["detail"]