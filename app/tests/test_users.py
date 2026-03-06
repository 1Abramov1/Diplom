import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestUsers:
    """Тесты пользователей"""

    async def test_get_me_authorized(self, client: AsyncClient, auth_headers, test_user):
        """Получение профиля авторизованным пользователем"""
        response = await client.get(
            "/api/v1/users/me",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["username"] == "testuser"
        assert data["id"] == test_user.id

    async def test_get_me_unauthorized(self, client: AsyncClient):
        """Получение профиля без авторизации"""
        response = await client.get("/api/v1/users/me")
        assert response.status_code == 401

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Получение профиля с неверным токеном"""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = await client.get("/api/v1/users/me", headers=headers)
        assert response.status_code == 401