from os import access

from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header, validate_access_token
from src.database.models.orders import Order, OrderItem, OrderStatusEnum
from src.database.models.shopping_carts import CartItem, Cart
from src.database.routes.accounts import get_user_by_email, get_user_by_id
from src.database.routes.movies import get_movie_by_id
from src.database.schemas.orders import OrderItemCreateSchema, OrderCreateSchema, OrderResponseDetailSchema, \
    OrderCancelRequestSchema
from src.database import get_async_db

orders = APIRouter(
    prefix="/orders"
)


async def get_pending_order_by_user_id(user_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(Order).filter_by(user_id=user_id, status=OrderStatusEnum.PENDING)
    result = await db.execute(stmt)
    order_db = result.unique().scalar_one_or_none()
    return order_db


async def get_order_by_id(id: int, db: AsyncSession):
    stmt = select(Order).filter_by(id=id)
    result = await db.execute(stmt)
    order_db = result.unique().scalar_one_or_none()
    return order_db


async def get_order_item_by_order_id(order_id: int, db: AsyncSession):
    stmt = select(OrderItem.id).filter_by(order_id=order_id)
    result = await db.execute(stmt)
    order_item_db = result.scalars().all()
    return order_item_db


@orders.post(
    "/create_order/",
    response_model=OrderResponseDetailSchema,
    status_code=201
)
async def create_order(
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    stmt_cart = select(Cart).filter_by(user_id=user_id)
    result = await db.execute(stmt_cart)
    cart_db = result.unique().scalar_one_or_none()

    stmt_cart_item = select(CartItem).filter(CartItem.cart_id == cart_db.id)
    result = await db.execute(stmt_cart_item)
    cart_items_db = result.unique().scalars().all()

    if not cart_items_db:
        raise HTTPException(status_code=404, detail=f"Cart items in cart with id: {cart_db.id} not found")

    order_db = Order(
            user_id=user_id
        )
    db.add(order_db)
    await db.flush()

    for cart_item in cart_items_db:
        try:
            order_item_db = OrderItem(
                order_id=order_db.id,
                movie_id=cart_item.movie_id,
                price_at_order=cart_item.movie.price
            )
            db.add(order_item_db)
            await db.flush()
            order_db.total_amount += order_item_db.price_at_order
        except IntegrityError as exc:
            raise HTTPException(status_code=500, detail=str(exc))
    await db.commit()
    await db.refresh(order_db)
    return order_db


@orders.post("/cancel_order/", response_model=OrderResponseDetailSchema)
async def cancel_pending_order(
        order_cancel_schema: OrderCancelRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]

    stmt = select(Order).filter(Order.user_id == user_id, Order.id == order_cancel_schema.order_id)
    result = await db.execute(stmt)
    order_db = result.unique().scalar_one_or_none()
    if order_db.status == OrderStatusEnum.PENDING:
        order_db.status = OrderStatusEnum.CANCELED
        await db.commit()
        return order_db
    raise HTTPException(status_code=400, detail="You can cancel only pending order.")