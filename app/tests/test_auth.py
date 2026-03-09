import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestAuth:
    """Тесты авторизации"""

    async def test_register_success(self, client: AsyncClient):
        """Успешная регистрация с email"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "full_name": "New User",
                "password": "Newpass123!",
                "password_confirm": "Newpass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["full_name"] == "New User"
        assert "id" in data
        assert "password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient, test_user):
        """Регистрация с существующим email"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "full_name": "Another User",
                "password": "Newpass123!",
                "password_confirm": "Newpass123!",
            },
        )
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    async def test_register_duplicate_full_name(self, client: AsyncClient, test_user):
        """Регистрация с существующим full_name"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "another@example.com",
                "full_name": "Test User",
                "password": "Newpass123!",
                "password_confirm": "Newpass123!",
            },
        )
        assert response.status_code == 400
        assert "уже существует" in response.json()["detail"]

    async def test_login_success(self, client: AsyncClient, test_user):
        """Успешный логин"""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "Testpass123!"},
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
            data={"username": "test@example.com", "password": "wrongpass"},
        )
        assert response.status_code == 401
        assert "Неверный" in response.json()["detail"]

    async def test_login_wrong_username(self, client: AsyncClient):
        """Логин с неверным email"""
        response = await client.post(
            "/api/v1/auth/login",
            data={"username": "nonexistent@example.com", "password": "Testpass123!"},
        )
        assert response.status_code == 401
        assert "Неверный" in response.json()["detail"]

    async def test_register_with_phone_success(self, client: AsyncClient):
        """Регистрация с телефоном (без email)"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "phone": "+79991234567",
                "full_name": "Phone User",
                "password": "Newpass123!",
                "password_confirm": "Newpass123!",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["phone"] == "+79991234567"
        assert data["email"] is None
        assert data["full_name"] == "Phone User"

    async def test_register_invalid_phone(self, client: AsyncClient):
        """Регистрация с неверным телефоном"""
        test_cases = [
            ("12345", "слишком короткий"),
            ("abcdefg", "не цифры"),
            ("+7999", "неполный"),
            ("8aaa5555555", "с буквами"),
        ]

        for phone, description in test_cases:
            response = await client.post(
                "/api/v1/auth/register",
                json={
                    "phone": phone,
                    "full_name": f"User_{phone[:3]}",
                    "password": "Newpass123!",
                    "password_confirm": "Newpass123!",
                },
            )
            assert response.status_code == 422, f"Должен быть 422 для {description}: {phone}"

    async def test_login_with_phone(self, client: AsyncClient, test_user_with_phone):
        """Логин по телефону"""
        response = await client.post(
            "/api/v1/auth/login", data={"username": "+79991234567", "password": "Testpass123!"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["phone"] == "+79991234567"
        assert data["user"]["email"] is None

    async def test_login_with_phone_normalized(self, client: AsyncClient, test_user_with_phone):
        """Логин по телефону в разных форматах"""
        phone_formats = [
            "+79991234567",  # полный формат
            "89991234567",  # с 8 вместо +7
            "9991234567",  # без кода (10 цифр)
        ]

        for phone in phone_formats:
            response = await client.post("/api/v1/auth/login", data={"username": phone, "password": "Testpass123!"})
            assert response.status_code == 200, f"Не работает для формата: {phone}"
