from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header
from database.models.shopping_carts import Cart
from database.session import get_async_db

carts = APIRouter(
    prefix="/shopping_carts"
)


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


@carts.get("/carts/add_item/")
async def add_item_or_create_carts(
        db: AsyncSession = Depends(get_async_db),
        header: str = Depends(authorization_header),
):

    stmt = select(Cart).filter_by(user_id=1)
    result = await db.execute(stmt)
    cart_db = result.unique().scalar_one_or_none()
    return cart_db

