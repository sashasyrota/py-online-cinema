from decimal import Decimal

from fastapi import APIRouter
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.movies import Movie, Certification, Genre, Director, Star
from database.schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema
from database.session import get_async_db

movies = APIRouter(
    prefix="/theater"
)


@movies.get("/movies/", response_model=list[MovieListResponseSchema])
async def get_movies(db: AsyncSession = Depends(get_async_db)):
    stmt = select(Movie)
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.get("/movies/{pk:int}/")
async def get_movie_detail(pk: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(Movie).filter_by(id=pk)
    result = await db.execute(stmt)
    movies_db = result.unique().scalar_one_or_none()
    return movies_db



