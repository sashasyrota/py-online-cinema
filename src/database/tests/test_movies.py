import decimal
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.database.models import Genre, Star, Movie, Comment, User
from src.database.schemas.movies import (
    GenreStarResponseSchema,
    MovieDetailResponseSchema,
    GenreStarDetailResponseSchema,
    MovieListResponseSchema,
    MovieCommentListResponseSchema,
    CommentResponseSchema,
    ReplyCommentResponseSchema,
)

movie_prefix = "/api/v1/theater/"


def get_test_movie_data(name: str = "Testmovie1", certification_id: int = 1):
    return {
        "name": name,
        "year": 2000,
        "time": 90,
        "price": 10,
        "certification": certification_id,
        "votes": 1,
        "genres": [],
        "gross": 4.6,
        "directors": [],
        "stars": [],
        "meta_score": 4.6,
        "description": "test_description",
    }


async def func_test_with_sorting(client):
    response = await client.get(f"{movie_prefix}movies/")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name"

    response = await client.get(f"{movie_prefix}movies/?sort_by=name")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name"

    response = await client.get(f"{movie_prefix}movies/?sort_by=year")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name1"

    response = await client.get(f"{movie_prefix}movies/?sort_by=imdb")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name1"

    response = await client.get(f"{movie_prefix}movies/?sort_by=price")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name1"


async def func_test_with_filtering(client, genre_id, director_id):
    response = await client.get(f"{movie_prefix}movies/?price=10.9")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert decode_response[0]["name"] == "Test_movie_name3"

    response = await client.get(f"{movie_prefix}movies/?min_rating=10")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 2

    response = await client.get(f"{movie_prefix}movies/?year=1990")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 2

    response = await client.get(f"{movie_prefix}movies/?name=name3")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 1
    assert decode_response[0]["name"] == "Test_movie_name3"

    response = await client.get(f"{movie_prefix}movies/?genres={genre_id}")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 2
    assert decode_response[0]["name"] == "Test_movie_name"
    assert decode_response[1]["name"] == "Test_movie_name1"

    response = await client.get(
        f"{movie_prefix}movies/?directors={director_id}"
    )
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 1
    assert decode_response[0]["name"] == "Test_movie_name"

    response = await client.get(f"{movie_prefix}movies/?stars={director_id}")
    decode_response = json.loads(response.content.decode())
    assert response.status_code == 200
    assert len(decode_response) == 1
    assert decode_response[0]["name"] == "Test_movie_name2"


class TestUnauthorized:

    @pytest.mark.asyncio
    async def test_movies_list(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        await create_movie(certification_id=certification_db.id)
        await create_movie(
            name="Test_movie_name1", certification_id=certification_db.id
        )
        response = await client.get(f"{movie_prefix}movies/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 2

    @pytest.mark.asyncio
    async def test_movies_list_with_pagination(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        await create_movie(certification_id=certification_db.id)
        movie_db1 = await create_movie(
            name="Test_movie_name1", certification_id=certification_db.id
        )
        response = await client.get(f"{movie_prefix}movies/?per_page=1")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 1

        response = await client.get(f"{movie_prefix}movies/?per_page=1&page=2")
        decode_response = json.loads(response.content.decode())
        assert len(decode_response) == 1
        assert response.status_code == 200
        movie_name = movie_db1.name
        assert movie_name in decode_response[0]["name"]

    @pytest.mark.asyncio
    async def test_movies_list_with_sorting(
        self, client: AsyncClient, create_movie, create_certification, db
    ):
        certification_db = await create_certification()
        await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
        )
        movie_db1 = await create_movie(
            name="Test_movie_name1",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("9.8"),
        )
        movie_db1.imdb = 10
        await db.commit()
        await func_test_with_sorting(client)

    @pytest.mark.asyncio
    async def test_movies_list_with_filtering(
        self,
        client: AsyncClient,
        create_movie,
        create_certification,
        create_genre,
        create_director,
        create_star,
        db,
    ):
        certification_db = await create_certification()
        genre_db = await create_genre()
        genre1_db = await create_genre(name="test_genre1")
        director_db = await create_director()
        star_db = await create_star()
        await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            genres=[genre_db, genre1_db],
            directors=[director_db],
        )
        movie_db1 = await create_movie(
            name="Test_movie_name1",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("9.80"),
            genres=[genre_db],
        )
        await create_movie(
            name="Test_movie_name2",
            certification_id=certification_db.id,
            stars=[star_db],
        )
        movie_db4 = await create_movie(
            name="Test_movie_name3",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("10.90"),
        )
        movie_db4.imdb = 10
        movie_db1.imdb = 10
        await db.commit()

        await func_test_with_filtering(client, genre_db.id, director_db.id)

    @pytest.mark.asyncio
    async def test_movie_detail(
        self,
        client: AsyncClient,
        db,
        create_movie,
        create_certification,
        create_genre,
        create_director,
        create_star,
    ):
        certification_db = await create_certification()
        genre_db = await create_genre()
        director_db = await create_director()
        test_movie = await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            genres=[genre_db],
            directors=[director_db],
        )
        stmt = select(Movie).filter_by(id=test_movie.id)
        result = await db.execute(stmt)
        movie_db = result.unique().scalar_one_or_none()

        response = await client.get(f"{movie_prefix}movies/{test_movie.id}/")
        decode_response = response.content.decode()
        assert response.status_code == 200
        movie_schema = MovieDetailResponseSchema.model_validate(movie_db)
        assert decode_response == movie_schema.model_dump_json()

    @pytest.mark.asyncio
    async def test_update_movie_is_staff_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.put(
            f"{movie_prefix}movies/{test_movie.id}/",
            json=get_test_movie_data(),
        )

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_create_movie_is_staff_required(self, client: AsyncClient):
        response = await client.post(
            f"{movie_prefix}movies/", json=get_test_movie_data()
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_delete_movie_is_staff_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.delete(
            f"{movie_prefix}movies/{test_movie.id}/"
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_get_favourite_movies_is_authenticated_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        await create_movie(certification_id=certification_db.id)
        response = await client.get(f"{movie_prefix}favourite_movies/")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_add_or_remove_favourite_movies_is_authenticated_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/add_or_remove_from_favourite/",
            json={"movie_id": test_movie.id},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_rate_movie_is_authenticated_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/rate_movie/",
            json={"rate": 4},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_like_movie_is_authenticated_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/like/"
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_dislike_movie_is_authenticated_required(
        self, client: AsyncClient, create_movie, create_certification
    ):
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/dislike/"
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_get_comment_list(
        self,
        client: AsyncClient,
        create_movie,
        create_certification,
        create_comment,
        create_user,
        db,
    ):
        user_db = await create_user()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        await create_comment(
            user_id=user_db.id,
            movie_id=movie_db.id,
        )
        await create_comment(
            user_id=user_db.id,
            movie_id=movie_db.id,
        )
        response = await client.get(
            f"{movie_prefix}movies/comments/{movie_db.id}/"
        )
        stmt = select(Comment).filter_by(movie_id=movie_db.id)
        result = await db.execute(stmt)
        comments_db = result.unique().scalars().all()
        result_db = [
            MovieCommentListResponseSchema.model_validate(comment).model_dump()
            for comment in comments_db
        ]
        assert result_db == response.json()

    @pytest.mark.asyncio
    async def test_create_comment_is_auth_required(
        self, client: AsyncClient, create_movie, create_certification, db
    ):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{movie_db.id}/create_comment/",
            json={
                "text": "test_text",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_reply_comment_is_auth_required(
        self,
        client: AsyncClient,
        create_movie,
        create_certification,
        db,
        create_comment,
        create_user,
    ):
        user_db = await create_user()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        comment_db = await create_comment(
            user_id=user_db.id,
            movie_id=movie_db.id,
        )
        response = await client.post(
            f"{movie_prefix}movies/reply_comment/",
            json={
                "comment_id": comment_db.id,
                "reply_text": "test_reply_text",
            },
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_like_comment_is_auth_required(
        self,
        client: AsyncClient,
        create_movie,
        create_certification,
        db,
        create_comment,
        create_user,
    ):
        user_db = await create_user()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        comment_db = await create_comment(
            user_id=user_db.id,
            movie_id=movie_db.id,
        )
        response = await client.post(
            f"{movie_prefix}movies/like_comment/{comment_db.id}/",
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_dislike_comment_is_auth_required(
        self,
        client: AsyncClient,
        create_movie,
        create_certification,
        db,
        create_comment,
        create_user,
    ):
        user_db = await create_user()
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        comment_db = await create_comment(
            user_id=user_db.id,
            movie_id=movie_db.id,
        )
        response = await client.post(
            f"{movie_prefix}movies/dislike_comment/{comment_db.id}/",
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_genres_list(self, client: AsyncClient, create_genre, db):
        await create_genre()
        await create_genre(name="test_genre1")
        response = await client.get(f"{movie_prefix}genres/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200

        stmt = select(Genre)
        result = await db.execute(stmt)
        genres_db = result.unique().scalars().all()
        result_db = [
            GenreStarResponseSchema.model_validate(genre_db).model_dump()
            for genre_db in genres_db
        ]
        assert decode_response == result_db

    @pytest.mark.asyncio
    async def test_get_genre_detail(
        self,
        client: AsyncClient,
        create_genre,
        create_certification,
        create_movie,
        db,
    ):
        test_genre = await create_genre()
        certification_db = await create_certification()
        await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            genres=[test_genre],
        )
        stmt = select(Genre).filter_by(id=test_genre.id)
        result = await db.execute(stmt)
        genre_db = result.unique().scalar_one_or_none()

        response = await client.get(f"{movie_prefix}genres/{test_genre.id}/")
        decode_response = response.content.decode()
        genre_schema = GenreStarDetailResponseSchema.model_validate(genre_db)
        assert decode_response == genre_schema.model_dump_json()
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_movies_in_genre(
        self,
        client: AsyncClient,
        create_genre,
        create_certification,
        create_movie,
        db,
    ):
        test_genre = await create_genre()
        test_certification = await create_certification()
        await create_movie(certification_id=test_certification.id)
        await create_movie(
            name="Test_movie1_name",
            certification_id=test_certification.id,
            genres=[test_genre],
        )
        response = await client.get(
            f"{movie_prefix}movies_in_genre/{test_genre.id}/"
        )
        decode_response = response.json()
        stmt = select(Movie).filter(
            Movie.genres.any(Genre.id == test_genre.id)
        )
        result = await db.execute(stmt)
        movies_db = result.unique().scalars().all()
        result_db = [
            MovieListResponseSchema.model_validate(movie_db).model_dump()
            for movie_db in movies_db
        ]
        assert response.status_code == 200
        assert result_db == decode_response

    @pytest.mark.asyncio
    async def test_update_genre_is_staff_required(
        self, client: AsyncClient, create_genre
    ):
        test_genre = await create_genre()
        response = await client.put(
            f"{movie_prefix}genres/{test_genre.id}/",
            json={"name": "TestGenre1"},
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_create_genre_is_staff_required(self, client: AsyncClient):
        response = await client.post(
            f"{movie_prefix}genres/", json={"name": "TestGenre1"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_delete_genre_is_staff_required(
        self, client: AsyncClient, create_genre
    ):
        test_genre = await create_genre()
        response = await client.delete(
            f"{movie_prefix}genres/{test_genre.id}/"
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_stars_list(self, client: AsyncClient, create_star, db):
        await create_star()
        await create_star(name="test_star1")
        response = await client.get(f"{movie_prefix}stars/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200

        stmt = select(Star)
        result = await db.execute(stmt)
        stars_db = result.unique().scalars().all()
        result_db = [
            GenreStarResponseSchema.model_validate(star_db).model_dump()
            for star_db in stars_db
        ]
        assert decode_response == result_db

    @pytest.mark.asyncio
    async def test_get_star_detail(self, client: AsyncClient, create_star, db):
        test_star = await create_star()
        response = await client.get(f"{movie_prefix}stars/{test_star.id}/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200

        stmt = select(Star).filter_by(id=test_star.id)
        result = await db.execute(stmt)
        star_db = result.unique().scalar_one_or_none()
        result_db = GenreStarDetailResponseSchema.model_validate(
            star_db
        ).model_dump()
        assert decode_response == result_db

    @pytest.mark.asyncio
    async def test_update_star_is_staff_required(
        self, client: AsyncClient, create_star
    ):
        test_star = await create_star()
        response = await client.put(
            f"{movie_prefix}stars/{test_star.id}/", json={"name": "Teststar1"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_create_star_is_staff_required(self, client: AsyncClient):
        response = await client.post(
            f"{movie_prefix}stars/", json={"name": "Teststar1"}
        )
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"

    @pytest.mark.asyncio
    async def test_delete_star_is_staff_required(
        self, client: AsyncClient, create_star
    ):
        test_star = await create_star()
        response = await client.delete(f"{movie_prefix}stars/{test_star.id}/")
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authorized"


class TestAuthorized:

    @pytest.mark.asyncio
    async def test_add_remove_and_get_favourite_movies(
        self,
        create_movie,
        create_certification,
        create_user,
        db,
        client: AsyncClient,
        get_access_token_and_user_id,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        test_certification = await create_certification()
        test_movie = await create_movie(certification_id=test_certification.id)
        add_response = await client.post(
            f"{movie_prefix}movies/add_or_remove_from_favourite/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"movie_id": test_movie.id},
        )
        assert add_response.status_code == 200
        stmt = select(Movie).filter(
            Movie.who_add_to_favourite.any(User.id == user_id)
        )
        result = await db.execute(stmt)
        movies_db = result.unique().scalars().all()
        assert movies_db[0].id == test_movie.id

        get_response = await client.get(
            f"{movie_prefix}favourite_movies/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        result_db = [
            MovieListResponseSchema.model_validate(movie).model_dump()
            for movie in movies_db
        ]
        assert result_db == get_response.json()
        assert get_response.status_code == 200

        remove_response = await client.post(
            f"{movie_prefix}movies/add_or_remove_from_favourite/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"movie_id": test_movie.id},
        )
        assert remove_response.status_code == 200
        stmt = select(Movie).filter(
            Movie.who_add_to_favourite.any(User.id == user_id)
        )
        result = await db.execute(stmt)
        movies_db = result.unique().scalars().all()
        assert movies_db == []

    @pytest.mark.asyncio
    async def test_get_favourite_movies_with_params(
        self,
        create_movie,
        create_certification,
        create_user,
        db,
        client: AsyncClient,
        create_genre,
        create_director,
        create_star,
    ):
        user_db = await create_user()
        user_db.is_active = True
        certification_db = await create_certification()
        genre_db = await create_genre()
        genre1_db = await create_genre(name="test_genre1")
        director_db = await create_director()
        star_db = await create_star()
        movie_db = await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            genres=[genre_db, genre1_db],
            directors=[director_db],
        )
        movie_db1 = await create_movie(
            name="Test_movie_name1",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("9.80"),
            genres=[genre_db],
        )
        await create_movie(
            name="Test_movie_name2",
            certification_id=certification_db.id,
            stars=[star_db],
        )
        movie_db4 = await create_movie(
            name="Test_movie_name3",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("10.90"),
        )
        movie_db4.imdb = 10
        movie_db1.imdb = 10
        await db.flush()
        await db.refresh(user_db)
        user_db.favourite_movies.extend([movie_db, movie_db1])
        await db.commit()
        login_response = await client.post(
            f"/api/v1/accounts/login/",
            json={"email": user_db.email, "password": "Testtest1221!"},
        )
        access_token = login_response.json()["access_token"]
        add_response = await client.get(
            f"{movie_prefix}favourite_movies/",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        stmt = select(Movie).filter(
            Movie.who_add_to_favourite.any(User.id == user_db.id)
        )
        result = await db.execute(stmt)
        movies_db = result.unique().scalars().all()

        result_db = [
            MovieListResponseSchema.model_validate(movie).model_dump()
            for movie in movies_db
        ]
        assert add_response.status_code == 200
        assert result_db == add_response.json()

        await func_test_with_filtering(
            client, genre_db.id, certification_db.id
        )
        await func_test_with_sorting(client)

    @pytest.mark.asyncio
    async def test_update_genre_is_staff_required(
        self,
        create_genre,
        db,
        create_user,
        client: AsyncClient,
        get_access_token_and_user_id,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        test_genre = await create_genre()
        response = await client.put(
            f"{movie_prefix}genres/{test_genre.id}/",
            json={"name": "TestGenre1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You don`t have permission to this action"
        )

    @pytest.mark.asyncio
    async def test_create_genre_is_staff_required(
        self,
        create_user,
        db,
        client: AsyncClient,
        get_access_token_and_user_id,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        response = await client.post(
            f"{movie_prefix}genres/",
            json={"name": "TestGenre1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You don`t have permission to this action"
        )

    @pytest.mark.asyncio
    async def test_delete_genre_is_staff_required(
        self,
        create_genre,
        create_user,
        db,
        get_access_token_and_user_id,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        print(access_token)
        test_genre = await create_genre()
        response = await client.delete(
            f"{movie_prefix}genres/{test_genre.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "You don`t have permission to this action"
        )

    @pytest.mark.asyncio
    async def test_rate_movie(
        self,
        create_movie,
        create_rate,
        create_user,
        create_certification,
        get_access_token_and_user_id,
        db,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        user1_db = await create_user(email="testtest121@gmail.com")
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/rate_movie/",
            json={"rate": 4},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        await db.refresh(test_movie)
        assert test_movie.votes == 1
        assert test_movie.imdb == 4

        await create_rate(movie_id=test_movie.id, user_id=user1_db.id, rate=4)
        another_rate_response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/rate_movie/",
            json={"rate": 5},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert another_rate_response.status_code == 200
        await db.refresh(test_movie)
        assert test_movie.votes == 2
        assert test_movie.imdb == 4.5

    @pytest.mark.asyncio
    async def test_like_dislike_movie(
        self,
        create_movie,
        create_certification,
        get_access_token_and_user_id,
        db,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        like_response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/like/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert like_response.status_code == 200
        assert like_response.json() == {"like": True}
        stmt = select(Movie).filter_by(id=test_movie.id)
        result = await db.execute(stmt)
        movie_db = result.unique().scalar_one_or_none()
        assert user_id == movie_db.likes_movies[0].user_id

        unlike_response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/like/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert unlike_response.status_code == 200
        assert unlike_response.json() == {"like": False}

        await db.refresh(movie_db)
        assert movie_db.likes_movies == []

        await client.post(
            f"{movie_prefix}movies/{test_movie.id}/like/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        dislike_response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/dislike/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert dislike_response.status_code == 200
        assert dislike_response.json() == {"dislike": True}
        await db.refresh(movie_db)
        assert movie_db.likes_movies == []
        assert (
            movie_db.dislikes_movies[0].movie_id == movie_db.id
        ), "if movie already has dislike, like should delete dislike"

    @pytest.mark.asyncio
    async def test_create_movie_comment(
        self,
        create_movie,
        create_certification,
        get_access_token_and_user_id,
        db,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        response = await client.post(
            f"{movie_prefix}movies/{test_movie.id}/create_comment/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"text": "test_text"},
        )
        assert response.status_code == 200
        stmt = select(Comment).filter_by(movie_id=test_movie.id)
        result = await db.execute(stmt)
        comment_db = result.unique().scalar_one_or_none()
        assert (
            response.json()
            == CommentResponseSchema.model_validate(comment_db).model_dump()
        )

    @pytest.mark.asyncio
    async def test_reply_movie_comment(
        self,
        create_movie,
        create_certification,
        get_access_token_and_user_id,
        db,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        await client.post(
            f"{movie_prefix}movies/{test_movie.id}/create_comment/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"text": "test_text"},
        )
        stmt = select(Comment).filter_by(movie_id=test_movie.id)
        result = await db.execute(stmt)
        comment_db = result.unique().scalar_one_or_none()

        response = await client.post(
            f"{movie_prefix}movies/reply_comment/",
            headers={"Authorization": f"Bearer {access_token}"},
            json={"reply_text": "test_text1", "comment_id": comment_db.id},
        )
        stmt = select(Comment).filter_by(reply_comment_id=comment_db.id)
        result = await db.execute(stmt)
        reply_comment_db = result.unique().scalar_one_or_none()
        assert (
            response.json()
            == ReplyCommentResponseSchema.model_validate(
                reply_comment_db
            ).model_dump()
        )

    @pytest.mark.asyncio
    async def test_like_dislike_comment(
        self,
        create_movie,
        create_certification,
        create_comment,
        get_access_token_and_user_id,
        db,
        client: AsyncClient,
    ):
        access_token, user_id = await get_access_token_and_user_id()
        certification_db = await create_certification()
        test_movie = await create_movie(certification_id=certification_db.id)
        test_comment = await create_comment(
            user_id=user_id, movie_id=test_movie.id
        )
        like_response = await client.post(
            f"{movie_prefix}movies/like_comment/{test_comment.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert like_response.status_code == 200
        assert like_response.json() == {"like": True}
        stmt = select(Comment).filter_by(id=test_comment.id)
        result = await db.execute(stmt)
        comment_db = result.unique().scalar_one_or_none()
        assert user_id == comment_db.likes_comments[0].user_id

        unlike_response = await client.post(
            f"{movie_prefix}movies/like_comment/{test_comment.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert unlike_response.status_code == 200
        assert unlike_response.json() == {"like": False}

        await db.refresh(comment_db)
        assert comment_db.likes_comments == []

        await client.post(
            f"{movie_prefix}movies/like_comment/{test_comment.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        dislike_response = await client.post(
            f"{movie_prefix}movies/dislike_comment/{test_comment.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert dislike_response.status_code == 200
        assert dislike_response.json() == {"dislike": True}
        await db.refresh(comment_db)
        assert comment_db.likes_comments == []
        assert (
            comment_db.dislikes_comments[0].comment_id == comment_db.id
        ), "if comment already has dislike, like should delete dislike"


class TestModerator:

    @pytest.mark.asyncio
    async def test_create_movie(
        self,
        client,
        create_certification,
        get_access_token_and_moderator_id,
        db,
    ):
        access_token, moderator_id = await get_access_token_and_moderator_id()
        certification_db = await create_certification()
        response = await client.post(
            f"{movie_prefix}movies/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=get_test_movie_data(certification_id=certification_db.id),
        )
        assert response.status_code == 201
        stmt = select(Movie)
        result = await db.execute(stmt)
        movie_db = result.unique().scalar_one_or_none()
        assert (
            MovieDetailResponseSchema.model_validate(movie_db).model_dump()
            == response.json()
        )

        duplicate_response = await client.post(
            f"{movie_prefix}movies/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=get_test_movie_data(certification_id=certification_db.id),
        )
        assert duplicate_response.status_code == 400
        assert (
            duplicate_response.json()["detail"]
            == f"Movie with name: {get_test_movie_data()["name"]}, "
            f"year: {get_test_movie_data()["year"]}, "
            f"time: {get_test_movie_data()["time"]} already exist in db."
        )

    @pytest.mark.asyncio
    async def test_update_movie(
        self,
        client,
        create_certification,
        create_movie,
        get_access_token_and_moderator_id,
        db,
    ):
        test_certification = await create_certification()
        test_movie = await create_movie(certification_id=test_certification.id)
        access_token, moderator_id = await get_access_token_and_moderator_id()

        update_response = await client.put(
            f"{movie_prefix}movies/{test_movie.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=get_test_movie_data(
                name="Test_movie2", certification_id=test_certification.id
            ),
        )
        await db.refresh(test_movie)
        stmt = select(Movie)
        result = await db.execute(stmt)
        movie_db = result.unique().scalar_one_or_none()
        assert movie_db.name == "Test_movie2"
        assert update_response.status_code == 200

        duplicate_response = await client.put(
            f"{movie_prefix}movies/{test_movie.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
            json=get_test_movie_data(
                name="Test_movie2", certification_id=test_certification.id
            ),
        )
        assert duplicate_response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_star(
        self, db, get_access_token_and_moderator_id, client: AsyncClient
    ):
        access_token, moderator_id = await get_access_token_and_moderator_id()
        response = await client.post(
            f"{movie_prefix}stars/",
            json={"name": "Teststar1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        stmt = select(Star)
        result = await db.execute(stmt)
        stars_db = result.unique().scalar_one_or_none()

        assert response.status_code == 200
        assert (
            response.json()
            == GenreStarDetailResponseSchema.model_validate(
                stars_db
            ).model_dump()
        )

    @pytest.mark.asyncio
    async def test_update_star(
        self,
        create_star,
        get_access_token_and_moderator_id,
        client: AsyncClient,
        db,
    ):
        access_token, moderator_id = await get_access_token_and_moderator_id()
        test_star = await create_star()
        test_star1 = await create_star(name="test_star1")
        response = await client.put(
            f"{movie_prefix}stars/{test_star.id}/",
            json={"name": "Teststar1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        await db.refresh(test_star)
        assert (
            response.json()
            == GenreStarDetailResponseSchema.model_validate(
                test_star
            ).model_dump()
        )
        assert test_star.name == "Teststar1"

        duplicate_response = await client.put(
            f"{movie_prefix}stars/{test_star1.id}/",
            json={"name": "Teststar1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert duplicate_response.status_code == 400
        await db.refresh(test_star1)
        assert test_star1.name == "test_star1"

    @pytest.mark.asyncio
    async def test_delete_star(
        self,
        db,
        create_star,
        get_access_token_and_moderator_id,
        client: AsyncClient,
    ):
        access_token, _ = await get_access_token_and_moderator_id()
        test_star = await create_star()
        response = await client.delete(
            f"{movie_prefix}stars/{test_star.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        stmt = select(Star)
        result = await db.execute(stmt)
        stars = result.unique().scalar_one_or_none()
        assert response.status_code == 204
        assert stars is None

    @pytest.mark.asyncio
    async def test_create_genre(
        self, db, get_access_token_and_moderator_id, client: AsyncClient
    ):
        access_token, moderator_id = await get_access_token_and_moderator_id()
        response = await client.post(
            f"{movie_prefix}genres/",
            json={"name": "Testgenre1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        stmt = select(Genre)
        result = await db.execute(stmt)
        genres_db = result.unique().scalar_one_or_none()

        assert response.status_code == 200
        assert (
            response.json()
            == GenreStarDetailResponseSchema.model_validate(
                genres_db
            ).model_dump()
        )

    @pytest.mark.asyncio
    async def test_update_genre(
        self,
        create_genre,
        get_access_token_and_moderator_id,
        client: AsyncClient,
        db,
    ):
        access_token, moderator_id = await get_access_token_and_moderator_id()
        test_genre = await create_genre()
        test_genre1 = await create_genre(name="test_genre1")
        response = await client.put(
            f"{movie_prefix}genres/{test_genre.id}/",
            json={"name": "Testgenre1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200
        await db.refresh(test_genre)
        assert (
            response.json()
            == GenreStarDetailResponseSchema.model_validate(
                test_genre
            ).model_dump()
        )
        assert test_genre.name == "Testgenre1"

        duplicate_response = await client.put(
            f"{movie_prefix}genres/{test_genre1.id}/",
            json={"name": "Testgenre1"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert duplicate_response.status_code == 400
        await db.refresh(test_genre1)
        assert test_genre1.name == "test_genre1"

    @pytest.mark.asyncio
    async def test_delete_genre(
        self,
        db,
        create_genre,
        get_access_token_and_moderator_id,
        client: AsyncClient,
    ):
        access_token, _ = await get_access_token_and_moderator_id()
        test_genre = await create_genre()
        response = await client.delete(
            f"{movie_prefix}genres/{test_genre.id}/",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        stmt = select(Genre)
        result = await db.execute(stmt)
        genres = result.unique().scalar_one_or_none()
        assert response.status_code == 204
        assert genres is None
