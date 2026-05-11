import decimal
import io

import pytest
import pytest_asyncio
from PIL import Image
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine

from database.models import User, Genre, Star, Director, Certification, Movie, Comment, Rate, Cart, CartItem, Order, \
    OrderItem, OrderStatusEnum, PaymentStatusEnum, Payment, PaymentItem
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


@pytest_asyncio.fixture(scope="function")
async def get_access_token_and_user_id(client, db, create_user):
    async def access_token_obj():
        test_user = await create_user()
        test_user.is_active = True
        await db.commit()
        response = await client.post(f"/api/v1/accounts/login/", json={
            "email": test_user.email,
            "password": "Testtest1221!"
        })
        return (
            response.json()["access_token"],
            test_user.id
        )
    return access_token_obj


@pytest_asyncio.fixture(scope="function")
async def get_access_token_and_moderator_id(client, db, create_user):
    async def access_token_obj():
        test_user = await create_user()
        test_user.is_active = True
        test_user.group_id = 2
        await db.commit()
        response = await client.post(f"/api/v1/accounts/login/", json={
            "email": test_user.email,
            "password": "Testtest1221!"
        })
        return (
            response.json()["access_token"],
            test_user.id
        )
    return access_token_obj


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
async def create_comment(db):
    async def comment_obj( user_id: int, movie_id: int, text: str = "test_text", reply_comment_id: int = None):
        _db_comment = Comment(
            text=text,
            user_id=user_id,
            movie_id=movie_id,
            reply_comment_id=reply_comment_id
        )
        db.add(_db_comment)
        await db.commit()
        return _db_comment
    return comment_obj


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
            meta_score: float = 8.8,
            price: decimal.Decimal = "10.30",
            genres: list = None,
            directors: list = None,
            stars: list = None,
            is_deleted: bool = False
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
            meta_score=meta_score,
            description="test_description",
            price=price,
            certification_id=certification_id,
            genres=genres,
            directors=directors,
            stars=stars,
            is_deleted=is_deleted
        )
        db.add(db_movie)
        await db.commit()
        return db_movie
    return movie_obj


@pytest_asyncio.fixture(scope="function")
async def create_rate(db):
    async def rate_obj(movie_id, user_id, rate):
        _db_rate = Rate(
            movie_id=movie_id,
            user_id=user_id,
            rate=rate
        )
        db.add(_db_rate)
        await db.commit()
        return _db_rate
    return rate_obj


@pytest_asyncio.fixture(scope="function")
async def create_cart(db):
    async def cart_obj(movie_id, user_id):

        _db_cart = Cart(
            user_id=user_id
        )
        db.add(_db_cart)
        await db.flush()
        _db_cart_item = CartItem(
            cart_id=_db_cart.id,
            movie_id=movie_id
        )
        db.add(_db_cart_item)
        await db.commit()
        return _db_cart
    return cart_obj

@pytest_asyncio.fixture(scope="function")
async def create_order(db):
    async def order_obj(user_id, movie_id, price, status: OrderStatusEnum = OrderStatusEnum.PENDING):

        _db_order = Order(
            user_id=user_id,
            status=status,
            total_amount=price
        )
        db.add(_db_order)
        await db.flush()
        _db_order_item = OrderItem(
            order_id=_db_order.id,
            movie_id=movie_id,
            price_at_order=price,
        )
        db.add(_db_order_item)
        await db.commit()
        return _db_order
    return order_obj


@pytest_asyncio.fixture(scope="function")
async def create_payment(db):
    async def payment_obj(user_id, order_id, amount, status: PaymentStatusEnum = PaymentStatusEnum.SUCCESSFUL):
        _db_payment = Payment(
            user_id=user_id,
            order_id=order_id,
            status=status,
            amount=amount,
            external_payment_id="12831"
        )
        db.add(_db_payment)
        await db.flush()
        _db_payment_item = PaymentItem(
            price_at_payment=amount,
            payment_id=12232141,
            order_item_id=1
        )
        db.add(_db_payment_item)
        await db.commit()
        return _db_payment
    return payment_obj