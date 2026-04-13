import decimal

from pydantic import BaseModel, ConfigDict

from database.models.movies import Like


class MovieFieldListSchema(BaseModel):
    name: str


class LikeDislikeSchema(BaseModel):
    user_id: int


class CommentSchema(BaseModel):
    id: int


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    year: int
    time: int
    imdb: float
    votes: int
    price: decimal.Decimal
    certification: MovieFieldListSchema
    genres: list[MovieFieldListSchema] | None
    directors: list[MovieFieldListSchema] | None
    stars: list[MovieFieldListSchema] | None
    likes: list[LikeDislikeSchema]
    likes_count: int
    dislikes: list[LikeDislikeSchema]
    dislikes_count: int



class MovieDetailResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: str | None
    price: decimal.Decimal
    certification: MovieFieldListSchema
    genres: list[MovieFieldListSchema] | None
    directors: list[MovieFieldListSchema] | None
    stars: list[MovieFieldListSchema] | None
    likes: list[LikeDislikeSchema]
    likes_count: int
    dislikes: list[LikeDislikeSchema]
    dislikes_count: int
    comments: list[CommentSchema]


class MovieCommentCreationSchema(BaseModel):
    text: str