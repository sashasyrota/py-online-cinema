from typing import Optional

from asyncpg import UniqueViolationError
from celery.bin.result import result
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse, Response

from src.config.security.jwt_token import authorization_header, validate_access_token
from src.database.routes.movies import get_movie_by_id
from src.database.models.orders import OrderItem, OrderStatusEnum, Order
from src.database.models.shopping_carts import Cart, CartItem
from src.database.routes.accounts import get_user_by_id, validate_is_staff_user
from src.database.schemas.shopping_carts import CartItemCreateSchema, CartDetailResponseSchema, CartListResponseSchema
from src.database import get_async_db

carts = APIRouter(
    prefix="/shopping_carts"
)


async def get_card_by_user_id(user_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(Cart).filter_by(user_id=user_id)
    result = await db.execute(stmt)
    cart_db = result.unique().scalar_one_or_none()
    return cart_db


@carts.get("/carts/")
async def get_carts(
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    await validate_is_staff_user(header, db)
    stmt = select(Cart)
    result = await db.execute(stmt)
    carts_db = result.unique().scalars().all()
    return carts_db


@carts.get("/cart_detail/", response_model=CartDetailResponseSchema)
async def get_cart_detail(
        cart_id: int | None = None,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header=header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id=user_id, db=db)
    stmt = select(Cart).filter_by(user_id=user_id)
    if cart_id:
        if user_db.group_id == 3:
            stmt = select(Cart).filter_by(id=cart_id)
        else:
            raise HTTPException(status_code=403, detail="You dont have permission to this action")
    result = await db.execute(stmt)
    cart_db = result.unique().scalar_one_or_none()

    if not cart_db:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart_db

@carts.post("/carts/add_item/", response_model=CartListResponseSchema)
async def add_item_or_create_carts(
        cart_item_schema: CartItemCreateSchema,
        db: AsyncSession = Depends(get_async_db),
        header: str = Depends(authorization_header),
):
    access_token = validate_access_token(header=header)
    user_id = access_token["user_id"]
    cart_db = await get_card_by_user_id(user_id, db)
    movie_db = await get_movie_by_id(cart_item_schema.movie_id, db)
    if not movie_db:
        raise HTTPException(status_code=404, detail=f"Movie with id: {cart_item_schema.movie_id} not exist in db.")
    if movie_db.is_deleted:
        raise HTTPException(status_code=400, detail=f"You can`t add to cart deleted movie.")
    try:
        if not cart_db:
            cart_db = Cart(
                user_id=user_id
            )
            db.add(cart_db)
            await db.flush()

        paid_movie_stmt = select(Order).filter(
            Order.user_id == user_id,
            Order.status == OrderStatusEnum.PAID,
            Order.order_items.any(OrderItem.movie_id == cart_item_schema.movie_id)
        )
        result = await db.execute(paid_movie_stmt)
        paid_movie_db = result.unique().scalar_one_or_none()
        if paid_movie_db:
            raise HTTPException(status_code=400, detail=f"Movie with id: {cart_item_schema.movie_id} already purchased")
        stmt = select(CartItem).filter_by(cart_id=cart_db.id, movie_id=cart_item_schema.movie_id)
        result = await db.execute(stmt)
        search_card = result.unique().scalar_one_or_none()
        if search_card:
            raise HTTPException(status_code=400, detail=f"Movie with id: {cart_item_schema.movie_id} already exist in this cart.")

        await db.refresh(cart_db)
        cart_item_db = CartItem(
            movie_id=cart_item_schema.movie_id
        )
        cart_db.cart_items.append(cart_item_db)
        await db.commit()
        return cart_db

    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@carts.delete(
    "/carts/delete_item/{movie_id:int}/",
    status_code=204
)
async def delete_item_from_cart(
        movie_id: int,
        db: AsyncSession = Depends(get_async_db),
        header: str = Depends(authorization_header),
):
    access_token = validate_access_token(header=header)
    user_id = access_token["user_id"]
    cart_db = await get_card_by_user_id(user_id=user_id, db=db)
    if not cart_db:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} dont have cart")
    stmt = select(CartItem).filter_by(cart_id=cart_db.id, movie_id=movie_id)
    result = await db.execute(stmt)
    db_cart_item = result.unique().scalar_one_or_none()

    if db_cart_item:
        try:
            await db.delete(db_cart_item)
            await db.commit()
            return
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=404, detail="Cart_item not found")