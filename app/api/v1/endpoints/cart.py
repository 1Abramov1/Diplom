"""
Эндпоинты для управления корзиной покупателя.

Предоставляет возможности:
- Просмотр содержимого корзины
- Добавление товаров
- Изменение количества
- Удаление товаров
- Очистка корзины
- Оформление заказа из корзины
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.endpoints.users import get_current_user
from app.core.database import get_db
from app.models.cart import Cart as CartModel
from app.models.cart import CartItem as CartItemModel
from app.models.order import Order as OrderModel
from app.models.order import OrderItem as OrderItemModel
from app.models.product import Product as ProductModel
from app.models.user import User
from app.schemas.cart import CartItem, CartItemCreate, CartItemUpdate, CartWithTotal
from app.schemas.order import Order as OrderSchema

router = APIRouter(prefix="/cart", tags=["Cart"])


async def get_or_create_cart(db: AsyncSession, user: User) -> CartModel:
    """
    Получить корзину пользователя или создать новую.

    Args:
        db: Сессия базы данных
        user: Текущий пользователь

    Returns:
        CartModel: Корзина пользователя
    """
    result = await db.execute(
        select(CartModel)
        .where(CartModel.user_id == user.id)
        .options(selectinload(CartModel.items).selectinload(CartItemModel.product))
    )
    cart = result.scalar_one_or_none()

    if not cart:
        cart = CartModel(user_id=user.id)
        db.add(cart)
        await db.commit()
        await db.refresh(cart)

    return cart


@router.get("/", response_model=CartWithTotal)
async def get_cart(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Получить содержимое корзины текущего пользователя.

    Args:
        db: Сессия базы данных
        current_user: Текущий аутентифицированный пользователь

    Returns:
        CartWithTotal: Корзина с товарами и итоговой суммой
    """
    cart = await get_or_create_cart(db, current_user)

    # Пересчитываем итоги
    total_price = sum(item.product.price * item.quantity for item in cart.items if item.product)
    total_items = sum(item.quantity for item in cart.items)

    return {
        "id": cart.id,
        "user_id": cart.user_id,
        "created_at": cart.created_at,
        "updated_at": cart.updated_at,
        "items": cart.items,
        "total_price": total_price,
        "total_items": total_items,
    }


@router.post("/items", response_model=CartItem, status_code=status.HTTP_201_CREATED)
async def add_to_cart(
    item_data: CartItemCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Добавить товар в корзину.
    """
    # Проверяем существование товара
    result = await db.execute(select(ProductModel).where(ProductModel.id == item_data.product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Товар не найден")

    if not product.is_available:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Товар недоступен")

    if product.quantity < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно товара. Доступно: {product.quantity}"
        )

    # Получаем или создаем корзину
    cart = await get_or_create_cart(db, current_user)

    # Проверяем, есть ли уже такой товар в корзине
    result = await db.execute(
        select(CartItemModel)
        .where(CartItemModel.cart_id == cart.id)
        .where(CartItemModel.product_id == item_data.product_id)
    )
    existing_item = result.scalar_one_or_none()

    if existing_item:
        # Если товар уже есть - увеличиваем количество
        new_quantity = existing_item.quantity + item_data.quantity
        if product.quantity < new_quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=f"Недостаточно товара. Всего можно: {product.quantity}"
            )
        existing_item.quantity = new_quantity
        await db.commit()
        await db.refresh(existing_item)
        return existing_item
    else:
        # Если товара нет - создаем новый элемент
        cart_item = CartItemModel(cart_id=cart.id, product_id=item_data.product_id, quantity=item_data.quantity)
        db.add(cart_item)
        await db.commit()
        await db.refresh(cart_item)
        return cart_item


@router.put("/items/{item_id}", response_model=CartItem)
async def update_cart_item(
    item_id: int,
    item_data: CartItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Изменить количество товара в корзине.
    """
    # Получаем элемент корзины с загрузкой связанных данных
    result = await db.execute(
        select(CartItemModel)
        .where(CartItemModel.id == item_id)
        .options(selectinload(CartItemModel.cart), selectinload(CartItemModel.product))
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент корзины не найден")

    # Проверяем, что корзина принадлежит текущему пользователю
    if cart_item.cart.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")

    # Проверяем наличие товара
    if cart_item.product.quantity < item_data.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Недостаточно товара. Доступно: {cart_item.product.quantity}",
        )

    # Обновляем количество
    cart_item.quantity = item_data.quantity
    await db.commit()
    await db.refresh(cart_item)

    return cart_item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_cart(
    item_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)
):
    """
    Удалить товар из корзины.
    """
    # Получаем элемент корзины
    result = await db.execute(
        select(CartItemModel).where(CartItemModel.id == item_id).options(selectinload(CartItemModel.cart))
    )
    cart_item = result.scalar_one_or_none()

    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Элемент корзины не найден")

    # Проверяем, что корзина принадлежит текущему пользователю
    if cart_item.cart.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Доступ запрещен")

    await db.delete(cart_item)
    await db.commit()

    return None


@router.delete("/clear", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Очистить всю корзину.
    """
    cart = await get_or_create_cart(db, current_user)

    # Удаляем все элементы корзины
    for item in cart.items:
        await db.delete(item)

    await db.commit()

    return None


@router.post("/checkout", response_model=OrderSchema, status_code=status.HTTP_201_CREATED)
async def checkout(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Оформить заказ из текущей корзины.
    """
    # Получаем корзину с загруженными товарами
    result = await db.execute(
        select(CartModel)
        .where(CartModel.user_id == current_user.id)
        .options(selectinload(CartModel.items).selectinload(CartItemModel.product))
    )
    cart = result.scalar_one_or_none()

    if not cart or not cart.items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Корзина пуста")

    # Проверяем наличие всех товаров и собираем данные для заказа
    items_to_order = []
    total_price = 0.0

    for cart_item in cart.items:
        product = cart_item.product
        if not product.is_available:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Товар '{product.name}' недоступен")

        if product.quantity < cart_item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно товара '{product.name}'. Доступно: {product.quantity}",
            )

        items_to_order.append({"product_id": product.id, "quantity": cart_item.quantity, "price": product.price})
        total_price += product.price * cart_item.quantity

        # Уменьшаем количество на складе
        product.quantity -= cart_item.quantity
        if product.quantity == 0:
            product.is_available = False

    # Создаем заказ
    new_order = OrderModel(user_id=current_user.id, total_price=total_price, status="pending")
    db.add(new_order)
    await db.flush()

    # Создаем элементы заказа
    for item_data in items_to_order:
        order_item = OrderItemModel(order_id=new_order.id, **item_data)
        db.add(order_item)

    # Очищаем корзину
    for item in cart.items:
        await db.delete(item)

    await db.commit()

    # Загружаем созданный заказ с элементами
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == new_order.id)
        .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
    )
    created_order = result.scalar_one()

    return created_order
