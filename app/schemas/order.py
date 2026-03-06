from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.product import Product


class OrderItemBase(BaseModel):
    product_id: int
    quantity: int

class OrderItemCreate(OrderItemBase):
    pass

class OrderItem(OrderItemBase):
    id: int
    order_id: int
    price: float
    product: Optional[Product] = None

    class Config:
        from_attributes = True

class OrderBase(BaseModel):
    status: str = "pending"

class OrderCreate(BaseModel):
    items: List[OrderItemCreate]

class Order(OrderBase):
    id: int
    user_id: int
    total_price: float
    created_at: datetime
    updated_at: Optional[datetime] = None
    items: List[OrderItem] = None

    class Config:
        from_attributes = True

    def __init__(self, **data):
        super().__init__(**data)
        if self.items is None:
            self.items = []
