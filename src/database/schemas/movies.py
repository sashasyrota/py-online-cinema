import decimal

from pydantic import BaseModel, ConfigDict, Field

from database.models.movies import LikeMovie


class MovieFieldListSchema(BaseModel):
    name: str


class MovieBaseSchema(BaseModel):
    name: str
    year: int
    time: int
    imdb: float
    gross: float | None
    price: decimal.Decimal
    certification: MovieFieldListSchema
    genres: list[MovieFieldListSchema] | None
    directors: list[MovieFieldListSchema] | None
    stars: list[MovieFieldListSchema] | None


class LikeDislikeSchema(BaseModel):
    user_id: int


class CommentSchema(BaseModel):
    id: int

class MovieIdSchema(BaseModel):
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
    votes: int
    genres: list[int] | None
    directors: list[int] | None
    stars: list[int] | None


class MovieUpdateRequestSchema(MovieCreateRequestSchema):
    pass


class MovieCommentCreationSchema(BaseModel):
    text: str


class MovieCommentListResponseSchema(BaseModel):
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


class StarCreateSchema(BaseModel):
    name: str


class StarUpdateSchema(BaseModel):
    name: str