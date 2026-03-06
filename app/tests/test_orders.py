import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestOrders:
    """Тесты заказов"""

    async def test_create_order_success(self, client: AsyncClient, auth_headers, test_product):
        """Успешное создание заказа"""
        order_data = {
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 2
                }
            ]
        }
        response = await client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == 1  # test_user.id
        assert data["total_price"] == test_product.price * 2
        assert len(data["items"]) == 1
        assert data["items"][0]["product_id"] == test_product.id
        assert data["items"][0]["quantity"] == 2

    async def test_create_order_unauthorized(self, client: AsyncClient, test_product):
        """Создание заказа без авторизации"""
        order_data = {
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
        response = await client.post(
            "/api/v1/orders/",
            json=order_data
        )
        assert response.status_code == 401

    async def test_create_order_insufficient_stock(self, client: AsyncClient, auth_headers, test_product):
        """Создание заказа с количеством больше доступного"""
        order_data = {
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 100  # больше чем есть (10)
                }
            ]
        }
        response = await client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        assert response.status_code == 400
        assert "Недостаточно товара" in response.json()["detail"]

    async def test_create_order_product_not_found(self, client: AsyncClient, auth_headers):
        """Создание заказа с несуществующим товаром"""
        order_data = {
            "items": [
                {
                    "product_id": 999,
                    "quantity": 1
                }
            ]
        }
        response = await client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        assert response.status_code == 404

    async def test_get_my_orders(self, client: AsyncClient, auth_headers, test_product):
        """Получение списка своих заказов"""
        # Сначала создадим заказ
        order_data = {
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
        await client.post("/api/v1/orders/", json=order_data, headers=auth_headers)

        # Получаем список заказов
        response = await client.get("/api/v1/orders/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["user_id"] == 1

    async def test_get_order_by_id(self, client: AsyncClient, auth_headers, test_product):
        """Получение конкретного заказа"""
        # Создаём заказ
        order_data = {
            "items": [
                {
                    "product_id": test_product.id,
                    "quantity": 1
                }
            ]
        }
        create_response = await client.post(
            "/api/v1/orders/",
            json=order_data,
            headers=auth_headers
        )
        order_id = create_response.json()["id"]

        # Получаем заказ по ID
        response = await client.get(
            f"/api/v1/orders/{order_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == order_id
        assert len(data["items"]) == 1

    async def test_get_order_not_found(self, client: AsyncClient, auth_headers):
        """Получение несуществующего заказа"""
        response = await client.get(
            "/api/v1/orders/999",
            headers=auth_headers
        )
        assert response.status_code == 404