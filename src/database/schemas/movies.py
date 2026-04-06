import decimal

from pydantic import BaseModel, ConfigDict


class CertificationSchema(BaseModel):
    name: str


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


class MovieDetailResponseSchema(BaseModel):

    name: str
    year: int
    time: int
    imdb: float
    votes: int
    meta_score: float | None
    gross: float | None
    description: float | None
    price: decimal.Decimal
    certification: CertificationSchema
    genres: list[str] | None
    directors: list[str] | None
    stars: list[str] | None
