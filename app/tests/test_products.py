import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestProducts:
    """Тесты товаров"""

    async def test_get_products_empty(self, client: AsyncClient):
        """Получение пустого списка товаров"""
        response = await client.get("/api/v1/products/")
        assert response.status_code == 200
        assert response.json() == []

    async def test_create_product_as_admin(self, client: AsyncClient, admin_headers):
        """Создание товара админом"""
        product_data = {
            "name": "Новый товар",
            "description": "Описание товара",
            "price": 199.99,
            "quantity": 5,
            "is_available": True,
        }
        response = await client.post("/api/v1/products/", json=product_data, headers=admin_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Новый товар"
        assert data["price"] == 199.99
        assert data["quantity"] == 5
        assert "id" in data

    async def test_create_product_as_user(self, client: AsyncClient, auth_headers):
        """Создание товара обычным пользователем (должно быть запрещено)"""
        product_data = {"name": "Новый товар", "price": 199.99, "quantity": 5}
        response = await client.post("/api/v1/products/", json=product_data, headers=auth_headers)
        assert response.status_code == 403
        assert "Недостаточно прав" in response.json()["detail"]

    async def test_get_product_by_id(self, client: AsyncClient, test_product):
        """Получение товара по ID"""
        response = await client.get(f"/api/v1/products/{test_product.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_product.id
        assert data["name"] == test_product.name

    async def test_get_product_not_found(self, client: AsyncClient):
        """Получение несуществующего товара"""
        response = await client.get("/api/v1/products/999")
        assert response.status_code == 404

    async def test_update_product_as_admin(self, client: AsyncClient, admin_headers, test_product):
        """Обновление товара админом"""
        update_data = {"name": "Обновлённый товар", "price": 299.99, "quantity": 15}
        response = await client.put(
            f"/api/v1/products/{test_product.id}",
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Обновлённый товар"
        assert data["price"] == 299.99
        assert data["quantity"] == 15

    async def test_delete_product_as_admin(self, client: AsyncClient, admin_headers, test_product):
        """Удаление товара админом"""
        response = await client.delete(f"/api/v1/products/{test_product.id}", headers=admin_headers)
        assert response.status_code == 204

        # Проверяем что товар удалён
        get_response = await client.get(f"/api/v1/products/{test_product.id}")
        assert get_response.status_code == 404
