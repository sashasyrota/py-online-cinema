import asyncio
import os
from decimal import Decimal
from typing import Type, Annotated

from celery.bin.result import result
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.params import Depends
from pydantic import BaseModel
from sqlalchemy import select, delete
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from config.security.jwt_token import authorization_header, validate_access_token
from config.smtp.smtp_controller import sent_message
from database.models.accounts import User
from database.models.movies import Movie, Certification, Genre, Director, Star, LikeMovie, DislikeMovie, Comment, Rate, \
    LikeComment, DislikeComment
from database.routes.accounts import get_user_by_id
from database.schemas.movies import MovieListResponseSchema, MovieDetailResponseSchema, MovieCommentCreationSchema, \
    MovieFavouriteRequestSchema, RateRequestSchema, GenreStarResponseSchema, CommentReplySchema, \
    MovieCommentListResponseSchema, MovieCreateRequestSchema, MovieUpdateRequestSchema, GenreStarDetailResponseSchema, \
    GenreCreateSchema, GenreUpdateSchema, GenreStarResponseSchema, StarCreateSchema, StarUpdateSchema
from database.session import get_async_db


load_dotenv()

movies = APIRouter(
    prefix="/theater"
)


async def get_movie_by_id(movie_id: int, db: AsyncSession):
    stmt = select(Movie).filter_by(id=movie_id)
    result = await db.execute(stmt)
    db_movie = result.unique().scalar_one_or_none()
    return db_movie


async def get_model_db_by_id(model_obj, model_id, db):
    stmt = select(model_obj).filter_by(id=model_id)
    result = await db.execute(stmt)
    return result.unique().scalar_one_or_none()


async def get_model_list_by_ids(model_obj, model_list_ids, db):
    stmt_genres = select(model_obj).filter(model_obj.id.in_(model_list_ids))
    result_genre = await db.execute(stmt_genres)
    genres_db = result_genre.unique().scalars().all()
    return genres_db


async def get_like_dislike_movie_by_user_id(model_obj: Type[LikeMovie] | Type[DislikeMovie], movie_id: int, user_id: int, db: AsyncSession):
    stmt = select(model_obj).filter_by(user_id=user_id, movie_id=movie_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_like_dislike_comment_by_id(model_obj: Type[LikeComment] | Type[DislikeComment], comment_id: int, user_id: int, db: AsyncSession):
    stmt = select(model_obj).filter_by(user_id=user_id, comment_id=comment_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_comment_by_id(comment_id: int, db: AsyncSession):
    stmt = select(Comment).filter_by(id=comment_id)
    result = await db.execute(stmt)
    db_comment = result.unique().scalar_one_or_none()
    return db_comment


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


@movies.get("/movies/{movie_id:int}/", response_model=MovieDetailResponseSchema)
async def get_movie_detail(
        movie_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    movie_db = await get_movie_by_id(movie_id, db)
    return movie_db


@movies.post("/movies/")
async def create_movie(
        movie_params: MovieCreateRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    certification_db = await get_model_db_by_id(Certification, movie_params.certification, db)
    genres_db = await get_model_list_by_ids(Genre, movie_params.genres, db)
    directors_db = await get_model_list_by_ids(Director, movie_params.directors, db)
    stars_db = await get_model_list_by_ids(Star, movie_params.stars, db)

    movie_db = Movie(
        name=movie_params.name,
        year=movie_params.year,
        time=movie_params.time,
        imdb=movie_params.imdb,
        gross=movie_params.gross,
        price=movie_params.price,
        genres=genres_db,
        directors=directors_db,
        stars=stars_db,
        certification=certification_db,
        votes=movie_params.votes,
        description=movie_params.description
    )
    db.add(movie_db)
    await db.commit()
    return movie_db


@movies.put("/movies/{movie_id:int}/")
async def update_movie(
        movie_params: MovieUpdateRequestSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    certification_db = await get_model_db_by_id(Certification, movie_params.certification, db)
    genres_db = await get_model_list_by_ids(Genre, movie_params.genres, db)
    directors_db = await get_model_list_by_ids(Director, movie_params.directors, db)
    stars_db = await get_model_list_by_ids(Star, movie_params.stars, db)

    movie_db = Movie(
        name=movie_params.name,
        year=movie_params.year,
        time=movie_params.time,
        imdb=movie_params.imdb,
        gross=movie_params.gross,
        price=movie_params.price,
        votes=movie_params.votes,
        description=movie_params.description,
        genres=genres_db,
        directors=directors_db,
        stars=stars_db,
        certification=certification_db

    )
    db.add(movie_db)
    await db.commit()
    return movie_db


@movies.delete("/movies/{movie_id:int}/", status_code=204)
async def delete_movie(
        movie_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    movie_db = await get_movie_by_id(movie_id, db)
    if not movie_db:
        raise HTTPException(status_code=404, detail=f"Movie with this id: {movie_id} not exist in db")
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")
    try:
        await db.delete(movie_db)
        await db.commit()
        return {"Movie deleted": True}
    except IntegrityError as err:
        raise HTTPException(status_code=500, detail=str(err))


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


@movies.get("/genres/", response_model=list[GenreStarResponseSchema])
async def get_genres(
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Genre)
    result = await db.execute(stmt)
    genres_db = result.scalars().unique().all()
    return genres_db


@movies.get("/genres/{genre_id}/", response_model=GenreStarDetailResponseSchema)
async def get_genre_detail(
        genre_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Genre).filter_by(id=genre_id)
    result = await db.execute(stmt)
    genre_db = result.unique().scalar_one_or_none()
    return genre_db


@movies.get("/movies_in_genre/{genre_id:int}/")
async def get_movies_in_genre(
        genre_id: int,
        db: AsyncSession = Depends(get_async_db)
):
    stmt = select(Movie).filter(Movie.genres.any(Genre.id == genre_id))
    result = await db.execute(stmt)
    movies_db = result.scalars().unique().all()
    return movies_db


@movies.post("/genres/")
async def create_genre(
        genre_schema: GenreCreateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    genre_db = Genre(name=genre_schema.name)
    db.add(genre_db)
    await db.commit()
    return genre_db


@movies.post("/genres/{genre_id:int}/")
async def update_genre(
        genre_id: int,
        genre_schema: GenreUpdateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    stmt = select(Genre).filter_by(id=genre_id)
    result = await db.execute(stmt)
    genre_db = result.unique().scalar_one_or_none()
    if not genre_db:
        raise HTTPException(status_code=404, detail=f"Genre with id: {genre_id} not exist")

    genre_db.name = genre_schema.name
    await db.commit()
    return genre_db


@movies.delete("/genres/{genre_id:int}/", status_code=204)
async def delete_genre(
        genre_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db)
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")
    stmt = select(Genre).filter_by(id=genre_id)
    result = await db.execute(stmt)
    genre_db = result.unique().scalar_one_or_none()
    if not genre_db:
        raise HTTPException(status_code=404, detail=f"Genre with id: {genre_id} not exist in db")
    await db.delete(genre_db)
    await db.commit()


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
    dislike_obj = await get_like_dislike_movie_by_user_id(DislikeMovie, movie_id, user_id, db)
    like_obj = await get_like_dislike_movie_by_user_id(LikeMovie, movie_id, user_id, db)
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
        like_obj = LikeMovie(
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

    dislike_obj = await get_like_dislike_movie_by_user_id(DislikeMovie, movie_id, user_id, db)
    like_obj = await get_like_dislike_movie_by_user_id(LikeMovie, movie_id, user_id, db)

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
        dislike_obj = DislikeMovie(
            user_id=user_id,
            movie_id=movie_id
        )
        db.add(dislike_obj)
        await db.commit()
        return {"dislike": True}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@movies.get("/movies/comments/{movie_id:int}/", response_model=list[MovieCommentListResponseSchema])
async def movie_comment_list(
        movie_id: int,
        db: AsyncSession = Depends(get_async_db),
):
    stmt = select(Comment).filter_by(movie_id=movie_id)
    result = await db.execute(stmt)
    comments_db = result.unique().scalars().all()
    return comments_db


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
    return comment_db


@movies.post("/movies/reply_comment/")
async def reply_movie_comment(
        comment_reply_schema: CommentReplySchema,
        background_tasks: BackgroundTasks,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    stmt = select(Comment).filter_by(id=comment_reply_schema.comment_id)
    result = await db.execute(stmt)
    comment_db = result.unique().scalar_one_or_none()
    if not comment_db:
        raise HTTPException(status_code=404, detail=f"Comment with id: {comment_reply_schema.comment_id} not found")

    try:
        reply_comment = Comment(
            text=comment_reply_schema.reply_text,
            user_id=user_id,
            reply_comment_id=comment_reply_schema.comment_id,
            movie_id=comment_db.movie_id
        )
        db.add(reply_comment)
        await db.commit()
        background_tasks.add_task(
            sent_message,
            "You got an answer on your comment",
            "Very important",
            user_db.email
        )
        return reply_comment
    except IntegrityError as err:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(err))


@movies.post("/movies/like_comment/{comment_id:int}/")
async def like_movie_comment(
    comment_id: int,
    background_tasks: BackgroundTasks,
    header: str = Depends(authorization_header),
    db: AsyncSession = Depends(get_async_db),

):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    comment_db = await get_comment_by_id(comment_id, db)
    if not comment_db:
        raise HTTPException(status_code=404, detail=f"Comment with id: {comment_id} not found")
    dislike_obj = await get_like_dislike_comment_by_id(DislikeComment, comment_id, user_id, db)
    like_obj = await get_like_dislike_comment_by_id(LikeComment, comment_id, user_id, db)
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
        like_obj = LikeComment(
            user_id=user_id,
            comment_id=comment_id
        )
        db.add(like_obj)
        await db.commit()
        background_tasks.add_task(
            sent_message,
            "You got a like on your comment",
            "Very important",
            user_db.email
        )
        return {"like": True}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@movies.post("/movies/dislike_comment/{comment_id:int}/")
async def dislike_movie_comment(
    comment_id: int,
    background_tasks: BackgroundTasks,
    header: str = Depends(authorization_header),
    db: AsyncSession = Depends(get_async_db),

):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    comment_db = await get_comment_by_id(comment_id, db)
    if not comment_db:
        raise HTTPException(status_code=404, detail=f"Comment with id: {comment_id} not found")
    dislike_obj = await get_like_dislike_comment_by_id(DislikeComment, comment_id, user_id, db)
    like_obj = await get_like_dislike_comment_by_id(LikeComment, comment_id, user_id, db)
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
        dislike_obj = DislikeComment(
            user_id=user_id,
            comment_id=comment_id
        )
        db.add(dislike_obj)
        await db.commit()
        background_tasks.add_task(
            sent_message,
            "You got a dislike on your comment",
            "Very important",
            user_db.email
        )
        return {"dislike": True}
    except Exception as exc:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(exc))


@movies.get("/movies/stars/")
async def star_list(
        db: AsyncSession = Depends(get_async_db),
):
    stmt = select(Star)
    result = await db.execute(stmt)
    db_stars = result.unique().scalars().all()
    return db_stars


@movies.get("/movies/stars/{star_id:int}", response_model=GenreStarDetailResponseSchema)
async def star_detail(
        star_id: int,
        db: AsyncSession = Depends(get_async_db),
):
    star_db = await get_model_db_by_id(Star, model_id=star_id, db=db)
    return star_db


@movies.post("/movies/stars/")
async def create_star(
        star_schema: StarCreateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    star_db = Star(
        name=star_schema.name
    )
    db.add(star_db)
    await db.commit()
    return star_db


@movies.put("/movies/stars/{star_id:int}/")
async def update_star(
        star_id: int,
        star_schema: StarUpdateSchema,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    stmt = select(Star).filter_by(id=star_id)
    result = await db.execute(stmt)
    star_db = result.unique().scalar_one_or_none()
    if not star_db:
        raise HTTPException(status_code=404, detail=f"Genre with id: {star_id} not exist")
    star_db.name = star_schema.name
    db.add(star_db)
    await db.commit()
    return star_db


@movies.delete("/movies/stars/{star_id:int}/")
async def delete_star(
        star_id: int,
        header: str = Depends(authorization_header),
        db: AsyncSession = Depends(get_async_db),
):
    access_token = validate_access_token(header)
    user_id = access_token["user_id"]
    user_db = await get_user_by_id(user_id, db)
    if user_db.group_id == 1:
        raise HTTPException(status_code=403, detail="You don`t have permission to this action")

    stmt = select(Star).filter_by(id=star_id)
    result = await db.execute(stmt)
    star_db = result.unique().scalar_one_or_none()
    if not star_db:
        raise HTTPException(status_code=404, detail=f"Genre with id: {star_id} not exist")
    await db.delete(star_db)
    await db.commit()
    return star_db