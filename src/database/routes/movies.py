from decimal import Decimal
from typing import Type, Annotated

from fastapi import APIRouter, HTTPException
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header, validate_access_token
from database.models.accounts import User
from database.models.movies import Movie, Certification, Genre, Director, Star, Like, Dislike, Comment, Rate
from database.routes.accounts import get_user_by_id
from database.schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema, MovieCommentCreationSchema, \
    MovieFavouriteRequestSchema, RateRequestSchema, GenreResponseSchema
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


async def movies_params(
        min_rating: int | None = None,
        year: int | None = None,
        price: str | None = None,
        genres: str | None = None,
        name: str | None = None,
        stars: str | None = None,
        directors: str | None = None,
        sort_by: str | None = None,
        page: int | None = 1,
        per_page: int | None = 10,
):
    return {
        "min_rating": min_rating,
        "year": year,
        "price": price,
        "genres": genres,
        "name": name,
        "stars": stars,
        "directors": directors,
        "sort_by": sort_by,
        "page": page,
        "per_page": per_page
    }

MovieParamsDep = Annotated[dict, Depends(movies_params)]


def get_stmt_with_query_params(movies_params: dict):
    stmt = select(Movie).limit(movies_params["per_page"]).offset(
        (movies_params["page"] - 1) * movies_params["per_page"])

    if movies_params["sort_by"]:
        if movies_params["sort_by"] == "name":
            stmt = stmt.order_by(Movie.name)
        elif movies_params["sort_by"] == "price":
            stmt = stmt.order_by(Movie.price)
        elif movies_params["sort_by"] == "year":
            stmt = stmt.order_by(Movie.year)
        elif movies_params["sort_by"] == "imdb":
            stmt = stmt.order_by(Movie.imdb)

    if movies_params["min_rating"]:
        stmt = stmt.filter(Movie.imdb >= movies_params["min_rating"])
    if movies_params["year"]:
        stmt = stmt.filter_by(year=movies_params["year"])
    if movies_params["price"]:
        stmt = stmt.filter_by(price=Decimal(movies_params["price"]))
    if movies_params["name"]:
        stmt = stmt.filter(Movie.name.ilike(f"%{movies_params["name"]}%"))
    if movies_params["genres"]:
        genres_list = [int(genre_id) for genre_id in movies_params["genres"].split(",")]
        stmt = stmt.filter(Movie.genres.any(Genre.id.in_(genres_list)))
    if movies_params["stars"]:
        stars_list = [int(star_id) for star_id in movies_params["stars"].split(",")]
        stmt = stmt.filter(Movie.stars.any(Star.id.in_(stars_list)))
    if movies_params["directors"]:
        directors_list = [int(director_id) for director_id in movies_params["directors"].split(",")]
        stmt = stmt.filter(Movie.directors.any(Director.id.in_(directors_list)))

    return stmt


@movies.get("/movies/", response_model=list[MovieListResponseSchema])
async def get_movies(
        movies_params: MovieParamsDep,
        db: AsyncSession = Depends(get_async_db)
):
    stmt = get_stmt_with_query_params(movies_params)
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.get("/favourite_movies/")
async def get_favourite_movies(
        movies_params: MovieParamsDep,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]

    stmt = get_stmt_with_query_params(movies_params)
    stmt = stmt.filter(Movie.who_add_to_favourite.any(User.id == user_id))
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.get("/genres/", response_model=list[GenreResponseSchema])
async def get_genres(
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Genre)
    result = await db.execute(stmt)
    genres_db = result.scalars().unique().all()
    return genres_db


@movies.get("/movies_in_genre/{genre_id:int}/")
async def get_movies_in_genre(
        genre_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Movie).filter(Movie.genres.any(Genre.id == genre_id))
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.get("/movies/{movie_id:int}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(movie_id: int, db: AsyncSession = Depends(get_async_db)):
    movie_db = await get_movie_by_id(movie_id, db)
    return movie_db


@movies.post("/movies/movie_id:int/add_to_remove_from_favourite/")
async def add_to_remove_from_favourite(
        add_to_favourite_schema: MovieFavouriteRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]

    movie_db = await get_movie_by_id(add_to_favourite_schema.movie_id, db)
    if not movie_db:
        raise HTTPException(status_code=404, detail=f"Movie with id: {add_to_favourite_schema.movie_id} not found")
    user_db = await get_user_by_id(user_id, db)

    try:
        if user_db in movie_db.who_add_to_favourite:
            movie_db.who_add_to_favourite.remove(user_db)
            await db.commit()
            return {f"{movie_db.id} movie delete from favourites": True}
        movie_db.who_add_to_favourite.append(user_db)
        await db.commit()
        return {f"{movie_db.id} movie add to favourites": True}
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@movies.post("/movies/movie_id:int/rate_movie/")
async def rate_movie(
        movie_id: int,
        rate_schema: RateRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]

    movie_db = await get_movie_by_id(movie_id, db)
    if not movie_db:
        raise HTTPException(status_code=404, detail=f"Movie with id: {movie_id} not found")
    rate = Rate(
        rate=rate_schema.rate,
        user_id=user_id,
        movie_id=movie_id
    )
    return rate


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


@movies.post("/movies/{movie_id:int}/create_comment/")
async def create_movie_comment(
        movie_schema: MovieCommentCreationSchema,
        movie_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    movie = await get_movie_by_id(movie_id, db)
    if not movie:
        raise HTTPException(status_code=404, detail=f"Movie with id: {movie_id} not found")
    try:
        comment_db = Comment(
            text=movie_schema.text,
            user_id=user_id,
            movie_id=movie_id
        )
        db.add(comment_db)
        await db.commit()
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))
