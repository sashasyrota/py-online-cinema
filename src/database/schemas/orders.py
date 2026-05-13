import datetime
import decimal

from pydantic import BaseModel, ConfigDict

from src.database.models.orders import OrderStatusEnum


class OrderItemCreateSchema(BaseModel):
    cart_id: int


class OrderCreateSchema(BaseModel):
    cart_item_ids: list[int]


class OrderCancelRequestSchema(BaseModel):
    order_id: int


class OrderItemDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    movie_id: int
    price_at_order: decimal.Decimal


class OrderResponseDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    created_at: datetime.datetime
    status: OrderStatusEnum
    total_amount: decimal.Decimal
    order_items: list[OrderItemDetailSchema]
