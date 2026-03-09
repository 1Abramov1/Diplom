"""
Схемы Pydantic для работы с корзиной покупателя.

Содержит схемы для:
- Товаров в корзине (CartItem)
- Операций с корзиной (добавление, обновление)
- Отображения корзины с товарами
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.product import Product

# ----- Cart Item Schemas -----


class CartItemBase(BaseModel):
    """
    Базовая схема для товара в корзине.

    Содержит минимальный набор полей, необходимых для идентификации товара
    и указания его количества в корзине.

    Attributes:
        product_id: Идентификатор товара в каталоге
        quantity: Количество единиц товара (минимум 1)
    """

    product_id: int
    quantity: int = 1


class CartItemCreate(CartItemBase):
    """
    Схема для добавления товара в корзину.

    Используется при POST-запросе на добавление товара.
    Наследует все поля от CartItemBase без изменений.

    Example:
        {
            "product_id": 123,
            "quantity": 2
        }
    """

    pass


class CartItemUpdate(BaseModel):
    """
    Схема для обновления количества товара в корзине.

    Используется при PUT-запросе для изменения количества
    уже существующего товара в корзине.

    Attributes:
        quantity: Новое количество товара (должно быть >= 1)

    Example:
        {
            "quantity": 3
        }
    """

    quantity: int


class CartItem(CartItemBase):
    """
    Схема для отображения товара в корзине.

    Используется при GET-запросах для получения информации
    о товарах в корзине. Включает данные о цене и связанном товаре.

    Attributes:
        id: Уникальный идентификатор записи в корзине
        cart_id: Идентификатор корзины
        price_at_time: Цена товара на момент добавления (если сохраняется)
        product: Полные данные о товаре из каталога

    Example:
        {
            "id": 1,
            "cart_id": 1,
            "product_id": 123,
            "quantity": 2,
            "price_at_time": 1500.99,
            "product": {
                "id": 123,
                "name": "Ноутбук",
                "price": 1500.99
            }
        }
    """

    id: int
    cart_id: int
    price_at_time: Optional[float] = None
    product: Optional[Product] = None

    model_config = ConfigDict(from_attributes=True)


# ----- Cart Schemas -----


class CartBase(BaseModel):
    """
    Базовая схема корзины.

    В текущей реализации не содержит дополнительных полей,
    но оставлена для возможного расширения в будущем.
    """

    pass


class Cart(CartBase):
    """
    Схема для отображения корзины со всеми товарами.

    Используется при GET-запросах для получения полной информации
    о корзине пользователя, включая список товаров.

    Attributes:
        id: Уникальный идентификатор корзины
        user_id: Идентификатор владельца корзины
        created_at: Дата и время создания корзины
        updated_at: Дата и время последнего обновления
        items: Список товаров в корзине

    Example:
        {
            "id": 1,
            "user_id": 1,
            "created_at": "2024-01-01T12:00:00",
            "updated_at": null,
            "items": [
                {
                    "id": 1,
                    "product_id": 123,
                    "quantity": 2,
                    "product": {
                        "name": "Ноутбук",
                        "price": 1500.99
                    }
                }
            ]
        }
    """

    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    items: List[CartItem] = ([],)

    model_config = ConfigDict(from_attributes=True)

    @property
    def total_price(self) -> float:
        """
        Вычисляет общую стоимость всех товаров в корзине.

        Returns:
            float: Сумма произведений цены на количество для каждого товара.
                   Если товар не загружен, его вклад в сумму равен 0.
        """
        return sum(item.product.price * item.quantity for item in self.items if item.product)

    @property
    def total_items(self) -> int:
        """
        Вычисляет общее количество товаров в корзине.

        Returns:
            int: Сумма количеств всех товаров в корзине.
        """
        return sum(item.quantity for item in self.items)


class CartWithTotal(Cart):
    """
    Расширенная схема корзины с предвычисленными итогами.

    Используется когда нужно гарантированно получить итоговые значения
    total_price и total_items в ответе (даже если они не были вычислены).

    Example:
        {
            "id": 1,
            "user_id": 1,
            "total_price": 3001.98,
            "total_items": 2,
            "items": [...]
        }
    """

    pass
