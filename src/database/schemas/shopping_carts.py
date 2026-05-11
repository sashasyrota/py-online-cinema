import datetime
import decimal

from pydantic import BaseModel, ConfigDict

from database.schemas.movies import MovieFieldListSchema


class CartItemCreateSchema(BaseModel):
    movie_id: int


class CartItemMovieSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    price: decimal.Decimal
    genres: list[MovieFieldListSchema] | None
    year: int


class CartItemDetailSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    added_at: datetime.datetime
    movie: CartItemMovieSchema


class CartDetailResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cart_items: list[CartItemDetailSchema]


class CartItemListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime.datetime
    movie_id: int


class CartListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    cart_items: list[CartItemListSchema]