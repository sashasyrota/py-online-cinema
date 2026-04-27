import datetime
import decimal

from pydantic import BaseModel

from database.schemas.movies import MovieFieldListSchema


class CartItemCreateSchema(BaseModel):
    movie_id: int


class CartItemMovieSchema(BaseModel):
    name: str
    price: decimal.Decimal
    genres: list[MovieFieldListSchema] | None
    year: int


class CartItemDetailSchema(BaseModel):
    added_at: datetime.datetime
    movie: CartItemMovieSchema


class CartDetailResponseSchema(BaseModel):
    id: int
    user_id: int
    cart_items: list[CartItemDetailSchema]


class CartItemListSchema(BaseModel):
    id: int
    added_at: datetime.datetime
    movie_id: int


class CartListResponseSchema(BaseModel):
    id: int
    user_id: int
    cart_items: list[CartItemListSchema]