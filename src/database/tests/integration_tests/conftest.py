import decimal
import io

import pytest
import pytest_asyncio
from PIL import Image
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine

from database.models import User, Genre, Star, Director, Certification, Movie
from database.session import reset_sqlite_database, get_sqlite_async_db, AsyncSqliteSessionLocal, sqlite_async_engine
from main import app


@pytest_asyncio.fixture(scope="function", autouse=True)
async def reset_db():
    await reset_sqlite_database()
    yield



@pytest_asyncio.fixture(scope="function")
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as async_client:
        yield async_client


@pytest_asyncio.fixture(scope="function")
async def db():
    async with AsyncSqliteSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def create_user(db):
    async def _db_user(email: str = "testtest1112111@gmail.com", password: str = "Testtest1221!"):
        db_user = User(
            email=email,
            group_id=1
        )
        db_user.password = password
        db.add(db_user)
        await db.commit()
        return db_user
    return _db_user


@pytest.fixture
def image_in_memory():
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='green')
    image.save(file, 'jpeg')
    file.name = 'test.jpg'
    file.seek(0)
    return file


@pytest.fixture
async def create_genre(db):
    async def genre_obj(name: str = "test_genre"):
        _db_genre = Genre(
            name=name
        )
        db.add(_db_genre)
        await db.commit()
        return _db_genre
    return genre_obj


@pytest.fixture
async def create_star(db):
    async def star_obj(name: str = "test_star"):
        _db_star = Star(
            name=name
        )
        db.add(_db_star)
        await db.commit()
        return _db_star
    return star_obj


@pytest.fixture
async def create_director(db):
    async def director_obj(name: str = "test_director"):
        _db_director = Director(
            name=name
        )
        db.add(_db_director)
        await db.commit()
        return _db_director
    return director_obj


@pytest.fixture
async def create_certification(db):
    async def certification_obj(name: str = "test_certification"):
        _db_certification = Certification(
            name=name
        )
        db.add(_db_certification)
        await db.commit()
        return _db_certification
    return certification_obj


@pytest_asyncio.fixture(scope="function")
async def create_movie(db):
    async def movie_obj(
            certification_id: int,
            name: str = "Test_movie_name",
            year: int = 2000,
            time: int = 90,
            imdb: int = 10,
            votes: int = 21,
            meta_score: float = 8.8,
            price: decimal.Decimal = decimal.Decimal("10.3"),
            genres: list = None,
            directors: list = None,
            stars: list = None
    ):
        if genres is None:
            genres = []

        if directors is None:
            directors = []

        if stars is None:
            stars = []

        db_movie = Movie(
            name=name,
            year=year,
            time=time,
            imdb=imdb,
            votes=votes,
            meta_score=meta_score,
            description="test_description",
            price=price,
            certification_id=certification_id,
            genres=genres,
            directors=directors,
            stars=stars
        )
        db.add(db_movie)
        await db.commit()
        return db_movie
    return movie_obj
    