import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


class TestIntegration:
    """Интеграционные тесты"""

    async def test_full_order_flow(self, client: AsyncClient, admin_headers, auth_headers):
        """Полный цикл: создание товара админом -> заказ пользователем"""

        # 1. Админ создаёт товар
        product_data = {
            "name": "Тестовый товар для интеграции",
            "description": "Описание",
            "price": 500.00,
            "quantity": 10,
            "is_available": True,
        }
        create_product = await client.post("/api/v1/products/", json=product_data, headers=admin_headers)
        assert create_product.status_code == 201
        product_id = create_product.json()["id"]

        # 2. Пользователь создаёт заказ
        order_data = {"items": [{"product_id": product_id, "quantity": 2}]}
        create_order = await client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
        assert create_order.status_code == 201
        order = create_order.json()
        assert order["total_price"] == 1000.00
        assert len(order["items"]) == 1

        # 3. Проверяем что количество товара уменьшилось
        get_product = await client.get(f"/api/v1/products/{product_id}")
        assert get_product.json()["quantity"] == 8

        # 4. Проверяем что заказ появился в списке
        get_orders = await client.get("/api/v1/orders/", headers=auth_headers)
        orders = get_orders.json()
        assert len(orders) >= 1
        assert orders[0]["id"] == order["id"]

    async def test_multiple_users_isolation(self, client: AsyncClient, test_user, test_admin):
        """Проверка изоляции данных между пользователями"""

        # Логинимся под первым пользователем
        login1 = await client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "Testpass123!"},
        )
        token1 = login1.json()["access_token"]
        headers1 = {"Authorization": f"Bearer {token1}"}

        # Логинимся под админом
        login2 = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin@example.com", "password": "Admin123!"},
        )
        token2 = login2.json()["access_token"]
        headers2 = {"Authorization": f"Bearer {token2}"}

        # Создаём заказ для первого пользователя
        # (нужен товар - создадим через админа)
        product_data = {"name": "Товар для изоляции", "price": 100, "quantity": 5}
        prod_resp = await client.post("/api/v1/products/", json=product_data, headers=headers2)
        product_id = prod_resp.json()["id"]

        # Первый пользователь создаёт заказ
        order_data = {"items": [{"product_id": product_id, "quantity": 1}]}
        await client.post("/api/v1/orders/", json=order_data, headers=headers1)

        # Проверяем что первый видит свой заказ
        orders1 = await client.get("/api/v1/orders/", headers=headers1)
        assert len(orders1.json()) == 1

        # Проверяем что второй НЕ видит заказ первого
        orders2 = await client.get("/api/v1/orders/", headers=headers2)
        assert len(orders2.json()) == 0
