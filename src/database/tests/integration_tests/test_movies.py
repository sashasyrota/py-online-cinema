import decimal
import json

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from database.models import Genre, Star, Director
from database.schemas.movies import GenreStarResponseSchema, MovieDetailResponseSchema
from database.tests.integration_tests.conftest import create_director

movie_prefix = "/api/v1/theater/"


class TestUnauthorized:

    @pytest.mark.asyncio
    async def test_movies_list(self, client: AsyncClient, create_movie, create_certification):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        movie_db1 = await create_movie(name="Test_movie_name1", certification_id=certification_db.id)
        response = await client.get(f"{movie_prefix}movies/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 2

    @pytest.mark.asyncio
    async def test_movies_list_with_pagination(self, client: AsyncClient, create_movie, create_certification):
        certification_db = await create_certification()
        movie_db = await create_movie(certification_id=certification_db.id)
        movie_db1 = await create_movie(name="Test_movie_name1", certification_id=certification_db.id)
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
    async def test_movies_list_with_sorting(self, client: AsyncClient, create_movie, create_certification):
        certification_db = await create_certification()
        movie_db = await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            imdb=8
        )
        movie_db1 = await create_movie(
            name="Test_movie_name1",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("9.8")
        )
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


    @pytest.mark.asyncio
    async def test_movies_list_with_filtering(
            self,
            client: AsyncClient,
            create_movie,
            create_certification,
            create_genre,
            create_director,
            create_star
    ):
        certification_db = await create_certification()
        genre_db = await create_genre()
        genre1_db = await create_genre(name="test_genre1")
        director_db = await create_director()
        star_db = await create_star()
        movie_db = await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            imdb=8,
            genres=[genre_db, genre1_db],
            directors = [director_db]
        )
        movie_db1 = await create_movie(
            name="Test_movie_name1",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("9.8"),
            genres=[genre_db]
        )
        movie_db3 = await create_movie(
            name="Test_movie_name2",
            certification_id=certification_db.id,
            imdb=8,
            stars=[star_db]
        )
        movie_db4 = await create_movie(
            name="Test_movie_name3",
            certification_id=certification_db.id,
            year=1990,
            price=decimal.Decimal("10.9")
        )
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

        response = await client.get(f"{movie_prefix}movies/?genres={genre_db.id}")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 2
        assert decode_response[0]["name"] == "Test_movie_name"
        assert decode_response[1]["name"] == "Test_movie_name1"

        response = await client.get(f"{movie_prefix}movies/?directors={director_db.id}")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 1
        assert decode_response[0]["name"] == "Test_movie_name"

        response = await client.get(f"{movie_prefix}movies/?stars={director_db.id}")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        assert len(decode_response) == 1
        assert decode_response[0]["name"] == "Test_movie_name2"

    @pytest.mark.asyncio
    async def test_movie_detail(
            self,
            client: AsyncClient,
            db,
            create_movie,
            create_certification,
            create_genre,
            create_director,
            create_star
    ):
        certification_db = await create_certification()
        genre_db = await create_genre()
        director_db = await create_director()
        movie_db = await create_movie(
            name="Test_movie_name",
            certification_id=certification_db.id,
            imdb=8,
            genres=[genre_db],
            directors=[director_db]
        )
        print(movie_db)
        response = await client.get(f"{movie_prefix}movies/{movie_db.id}/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200
        movie_schema = MovieDetailResponseSchema.model_validate(movie_db)
        print(movie_schema)

    @pytest.mark.asyncio
    async def test_genres_list(self, client: AsyncClient, create_genre, db):
        genre_db = await create_genre()
        genre1_db = await create_genre(name="test_genre1")
        response = await client.get(f"{movie_prefix}genres/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200

        stmt = select(Genre)
        result = await db.execute(stmt)
        genres_db = result.unique().scalars().all()
        result_db = [GenreStarResponseSchema.model_validate(genre_db).model_dump() for genre_db in genres_db]
        assert decode_response == result_db

    @pytest.mark.asyncio
    async def test_stars_list(self, client: AsyncClient, create_star, db):
        star_db = await create_star()
        star1_db = await create_star(name="test_star1")
        response = await client.get(f"{movie_prefix}stars/")
        decode_response = json.loads(response.content.decode())
        assert response.status_code == 200

        stmt = select(Star)
        result = await db.execute(stmt)
        stars_db = result.unique().scalars().all()
        result_db = [GenreStarResponseSchema.model_validate(star_db).model_dump() for star_db in stars_db]
        assert decode_response == result_db

