import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestCart:
    """Тесты для корзины"""

    async def test_add_to_cart(self, client: AsyncClient, auth_headers, test_product):
        """Добавление товара в корзину"""
        response = await client.post(
            "/api/v1/cart/items", json={"product_id": test_product.id, "quantity": 2}, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.json()
        assert data["product_id"] == test_product.id
        assert data["quantity"] == 2

    async def test_update_cart_item(self, client: AsyncClient, auth_headers, test_cart_item):
        """Обновление количества"""
        response = await client.put(
            f"/api/v1/cart/items/{test_cart_item.id}", json={"quantity": 5}, headers=auth_headers
        )
        assert response.status_code == 200
        assert response.json()["quantity"] == 5

    async def test_remove_from_cart(self, client: AsyncClient, auth_headers, test_cart_item):
        """Удаление товара из корзины"""
        item_id = test_cart_item.id
        response = await client.delete(f"/api/v1/cart/items/{item_id}", headers=auth_headers)
        assert response.status_code == 204

        # Проверяем что элемент удалён
        get_response = await client.get("/api/v1/cart/", headers=auth_headers)
        items = get_response.json()["items"]
        assert not any(item["id"] == item_id for item in items)
