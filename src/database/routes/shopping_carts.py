from asyncpg import UniqueViolationError
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse, Response

from config.security.jwt_token import authorization_header
from database.models.shopping_carts import Cart, CartItem
from database.schemas.shopping_carts import CartItemCreateSchema
from database.session import get_async_db

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
        db: AsyncSession = Depends(get_async_db),
        # header: str = Depends(authorization_header),

):
    stmt = select(Cart)
    result = await db.execute(stmt)
    carts_db = result.unique().scalars().all()
    return carts_db


@carts.get("/carts/{cart_id:int}/")
async def get_cart_detail(
        cart_id: int,
        # header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Cart).filter_by(id=1)
    result = await db.execute(stmt)
    cart_db = result.unique().scalar_one_or_none()
    return cart_db


@carts.post("/carts/add_item/")
async def add_item_or_create_carts(
        cart_item_schema: CartItemCreateSchema,
        db: AsyncSession = Depends(get_async_db),
        header: str = Depends(authorization_header),
):

    user_id = 39
    cart_db = await get_card_by_user_id(user_id, db)
    try:
        if not cart_db:
            cart_db = Cart(
                user_id=user_id
            )
            db.add(cart_db)
            await db.flush()
            cart_item_db = CartItem(
                cart_id=cart_db.id,
                movie_id=cart_item_schema.movie_id
            )
            db.add(cart_item_db)
            await db.commit()
            return cart_db

        stmt = select(CartItem).filter_by(cart_id=cart_db.id, movie_id=cart_item_schema.movie_id)
        result = await db.execute(stmt)
        search_card = result.unique().scalar_one_or_none()
        if search_card:
            raise UniqueViolationError

        cart_item_db = CartItem(
            cart_id=cart_db.id,
            movie_id=cart_item_schema.movie_id
        )
        db.add(cart_item_db)
        await db.commit()
        return cart_db

    except UniqueViolationError:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Movie with id: {cart_item_schema.movie_id} already exist in this cart.")

    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@carts.post("/carts/delete_item/{movie_id:int}/")
async def delete_item_from_cart(
        movie_id: int,
        db: AsyncSession = Depends(get_async_db),
        # header: str = Depends(authorization_header),
):
    user_id = 39
    cart_db = await get_card_by_user_id(user_id=user_id, db=db)
    if not cart_db:
        raise HTTPException(status_code=404, detail=f"User with id: {user_id} dont have cart")
    stmt = select(CartItem).filter_by(cart_id=cart_db.id, movie_id=movie_id)
    result = await db.execute(stmt)
    db_cart_item = result.scalar_one_or_none()

    if db_cart_item:
        try:
            await db.delete(db_cart_item)
            await db.commit()
            return Response(status_code=204)
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))
    raise HTTPException(status_code=404, detail="Cart_item not found")