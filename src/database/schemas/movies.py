import decimal

from fastapi import Depends
from pydantic import BaseModel, ConfigDict, Field, field_serializer, model_validator



class MovieFieldListSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str


class MovieBaseSchema(BaseModel):
    name: str
    year: int
    time: int
    gross: float | None
    price: decimal.Decimal
    certification: MovieFieldListSchema
    genres: list[MovieFieldListSchema] | None
    directors: list[MovieFieldListSchema] | None
    stars: list[MovieFieldListSchema] | None

    @field_serializer("price")
    def serialize_decimal_to_str(self, price: decimal.Decimal):
        return str(price)


class LikeDislikeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int | None


class CommentSchema(BaseModel):
    id: int

class MovieIdSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MovieListResponseSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    votes: int
    likes_movies: list[LikeDislikeSchema]
    likes_count: int
    dislikes_movies: list[LikeDislikeSchema]
    dislikes_count: int



class MovieDetailResponseSchema(MovieBaseSchema):
    model_config = ConfigDict(from_attributes=True)

    votes: int
    meta_score: float | None
    description: str | None
    likes_movies: list[LikeDislikeSchema]
    likes_count: int
    dislikes_movies: list[LikeDislikeSchema]
    dislikes_count: int
    comments: list[CommentSchema]


class MovieCreateRequestSchema(MovieBaseSchema):
    meta_score: float | None
    description: str | None
    certification: int
    genres: list[int] | None
    directors: list[int] | None
    stars: list[int] | None


class MovieUpdateRequestSchema(MovieCreateRequestSchema):
    pass


class MovieCommentCreationSchema(BaseModel):
    text: str


class MovieCommentListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    text: str
    movie_id: int
    reply_comment_id: int | None
    dislikes_comments: list[LikeDislikeSchema] | None
    likes_comments: list[LikeDislikeSchema] | None


class MovieFavouriteRequestSchema(BaseModel):
    movie_id: int


class RateRequestSchema(BaseModel):
    rate: int = Field(le=10, ge=0)


class GenreStarResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    movies_count: int


class GenreStarDetailResponseSchema(GenreStarResponseSchema):

    movies: list[MovieIdSchema]


class GenreCreateSchema(BaseModel):
    name: str


class GenreUpdateSchema(GenreCreateSchema):
    pass


class CommentReplySchema(BaseModel):
    comment_id: int
    reply_text: str


class CommentResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    movie_id: int
    user_id: int


class ReplyCommentResponseSchema(CommentResponseSchema):
    reply_comment_id: int


class StarCreateSchema(BaseModel):
    name: str


class StarUpdateSchema(BaseModel):
    name: str