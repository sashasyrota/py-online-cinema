import decimal

from pydantic import BaseModel, ConfigDict

from database.models.movies import Like


class CertificationSchema(BaseModel):
    name: str


class LikeDislikeSchema(BaseModel):
    user_id: int


class MovieListResponseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    year: int
    time: int
    imdb: float
    votes: int
    price: decimal.Decimal
    certification: CertificationSchema
    genres: list[str] | None
    directors: list[str] | None
    stars: list[str] | None
    likes: list[LikeDislikeSchema]
    likes_count: int
    dislikes: list[LikeDislikeSchema]
    dislikes_count: int



class MovieDetailResponseSchema(BaseModel):

    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: str | None
    price: decimal.Decimal
    certification: CertificationSchema
    genres: list[str] | None
    directors: list[str] | None
    stars: list[str] | None
