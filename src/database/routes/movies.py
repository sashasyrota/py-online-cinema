from decimal import Decimal
from typing import Type

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header, validate_access_token
from database.models.movies import Movie, Certification, Genre, Director, Star, Like, Dislike
from database.schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema
from database.session import get_async_db

movies = APIRouter(
    prefix="/theater"
)


async def get_movie_by_id(movie_id: int, db: AsyncSession):
    stmt = select(Movie).filter_by(id=movie_id)
    result = await db.execute(stmt)
    db_movie = result.unique().scalar_one_or_none()
    return db_movie


async def get_like_dislike_by_id(model_obj: Type[Like] | Type[Dislike], movie_id: int, user_id: int, db: AsyncSession):
    stmt = select(model_obj).filter_by(user_id=user_id, movie_id=movie_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


@movies.get("/movies/", response_model=list[MovieListResponseSchema])
async def get_movies(db: AsyncSession = Depends(get_async_db)):
    stmt = select(Movie)
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.get("/movies/{movie_id:int}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_async_db)):
    stmt = select(Movie).filter_by(id=movie_id)
    result = await db.execute(stmt)
    movies_db = result.unique().scalar_one_or_none()
    return movies_db


@movies.post("/movies/{movie_id:int}/like/")
async def like_movie(
        movie_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id: {movie_id} not found")
    dislike_obj = await get_like_dislike_by_id(Dislike, movie_id, user_id, db)
    like_obj = await get_like_dislike_by_id(Like, movie_id, user_id, db)
    if like_obj:
        try:
            await db.delete(like_obj)
            await db.commit()
            return {"like": False}
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))
    try:
        if dislike_obj:
            await db.delete(dislike_obj)
            await db.flush()
        like_obj = Like(
            user_id=user_id,
            movie_id=movie_id
        )
        db.add(like_obj)
        await db.commit()
        return {"like": True}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@movies.post("/movies/{movie_id:int}/dislike/")
async def dislike_movie(
        movie_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id: {movie_id} not found")

    dislike_obj = await get_like_dislike_by_id(Dislike, movie_id, user_id, db)
    like_obj = await get_like_dislike_by_id(Like, movie_id, user_id, db)

    if dislike_obj:
        try:
            await db.delete(dislike_obj)
            await db.commit()
            return {"dislike": False}
        except Exception as exc:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(exc))
    try:
        if like_obj:
            await db.delete(like_obj)
            await db.flush()
        dislike_obj = Dislike(
            user_id=user_id,
            movie_id=movie_id
        )
        db.add(dislike_obj)
        await db.commit()
        return {"dislike": True}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


