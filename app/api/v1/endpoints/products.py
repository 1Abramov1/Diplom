from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.product import Product as ProductModel
from app.schemas.product import Product, ProductCreate, ProductUpdate
from app.api.v1.endpoints.users import get_current_user
from app.models.user import User

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[Product])
async def get_products(
        skip: int = 0,
        limit: int = 100,
        db: AsyncSession = Depends(get_db)
):
    """Получить список всех товаров"""
    result = await db.execute(
        select(ProductModel).offset(skip).limit(limit)
    )
    products = result.scalars().all()
    return products


@router.get("/{product_id}", response_model=Product)
async def get_product(
        product_id: int,
        db: AsyncSession = Depends(get_db)
):
    """Получить товар по ID"""
    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    return product


@router.post("/", response_model=Product, status_code=status.HTTP_201_CREATED)
async def create_product(
        product_data: ProductCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)  # только авторизованные
):
    """Создать новый товар (только для авторизованных)"""
    # Проверяем права (можно добавить проверку на админа)
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )

    new_product = ProductModel(
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        quantity=product_data.quantity,
        is_available=product_data.is_available
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    return new_product


@router.put("/{product_id}", response_model=Product)
async def update_product(
        product_id: int,
        product_data: ProductUpdate,
        db: AsyncSession = Depends(get_db),current_user: User = Depends(get_current_user)  # только авторизованные
):
    """Обновить товар (только для авторизованных)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )

    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    # Обновляем только переданные поля
    update_data = product_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    await db.commit()
    await db.refresh(product)

    return product

@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)  # только авторизованные
):
    """Удалить товар (только для авторизованных)"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )

    result = await db.execute(
        select(ProductModel).where(ProductModel.id == product_id)
    )
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Товар не найден"
        )

    await db.delete(product)
    await db.commit()

    return None