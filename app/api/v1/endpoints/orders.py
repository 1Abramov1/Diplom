from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.core.database import get_db
from app.models.order import Order as OrderModel, OrderItem as OrderItemModel
from app.models.product import Product as ProductModel
from app.schemas.order import Order, OrderCreate, OrderItem
from app.api.v1.endpoints.users import get_current_user
from app.models.user import User

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=Order, status_code=status.HTTP_201_CREATED)
async def create_order(
        order_data: OrderCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Создать новый заказ (только для авторизованных)"""

    # Проверяем наличие товаров и считаем сумму
    total_price = 0.0
    items_to_create = []

    for item in order_data.items:
        # Получаем товар из базы
        result = await db.execute(
            select(ProductModel).where(ProductModel.id == item.product_id)
        )
        product = result.scalar_one_or_none()

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Товар с ID {item.product_id} не найден"
            )

        if not product.is_available:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Товар '{product.name}' недоступен"
            )

        if product.quantity < item.quantity:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Недостаточно товара '{product.name}'. Доступно: {product.quantity}"
            )

        # Уменьшаем количество на складе
        product.quantity -= item.quantity
        if product.quantity == 0:
            product.is_available = False

        total_price += product.price * item.quantity
        items_to_create.append({
            "product_id": product.id,
            "quantity": item.quantity,
            "price": product.price
        })

    # Создаём заказ
    new_order = OrderModel(
        user_id=current_user.id,
        total_price=total_price,
        status="pending"
    )

    db.add(new_order)
    await db.flush()  # чтобы получить id заказа

    # Создаём элементы заказа
    for item_data in items_to_create:
        order_item = OrderItemModel(
            order_id=new_order.id,
            **item_data
        )
        db.add(order_item)

    await db.commit()

    # Загружаем заказ с элементами для ответа
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == new_order.id)
        .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
    )
    created_order = result.scalar_one()

    return created_order


@router.get("/", response_model=List[Order])
async def get_my_orders(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить список своих заказов"""
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.user_id == current_user.id)
        .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
        .offset(skip)
        .limit(limit)
    )
    orders = result.scalars().all()
    return orders


@router.get("/{order_id}", response_model=Order)
async def get_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить информацию о заказе по ID"""
    result = await db.execute(
        select(OrderModel)
        .where(OrderModel.id == order_id)
        .where(OrderModel.user_id == current_user.id)
        .options(selectinload(OrderModel.items).selectinload(OrderItemModel.product))
    )
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заказ не найден"
        )

    return order