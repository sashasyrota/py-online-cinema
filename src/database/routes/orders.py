from os import access

from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header, validate_access_token
from database.models.orders import Order, OrderItem, OrderStatusEnum
from database.routes.movies import get_movie_by_id
from database.schemas.orders import OrderItemCreateSchema
from database.session import get_async_db

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


@orders.post("/create_order/")
async def create_order(
        order_item_schema: OrderItemCreateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    order_db = await get_pending_order_by_user_id(user_id=user_id, db=db)
    movie_db = await get_movie_by_id(
        movie_id=order_item_schema.movie_id,
        db=db
    )
    if not movie_db:
        raise HTTPException(status_code=404, detail=f"Movie with id: {order_item_schema.movie_id} not found")

    try:
        if order_db:

            stmt = select(OrderItem).filter_by(order_id=order_db.id, movie_id=movie_db.id)
            result = await db.execute(stmt)
            search_order_item = result.unique().scalar_one_or_none()
            if search_order_item:
                raise UniqueViolationError

            order_item_db = OrderItem(
                order_id=order_db.id,
                movie_id=movie_db.id,
                price_at_order=movie_db.price
            )
            db.add(order_item_db)
            order_db.total_amount += movie_db.price
            await db.commit()
            return order_db
        else:
            new_order_db = Order(
                user_id=user_id
            )
            db.add(new_order_db)
            await db.flush()
            order_item_db = OrderItem(
                order_id=new_order_db.id,
                movie_id=movie_db.id,
                price_at_order=movie_db.price
            )
            db.add(order_item_db)
            new_order_db.total_amount = movie_db.price
            await db.commit()
            return new_order_db

    except UniqueViolationError:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Movie with id: {order_item_schema.movie_id} already exist in this order.")
