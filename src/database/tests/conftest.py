import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine

from database.models import User
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
    async def _db_user(email: str, password: str):
        db_user = User(
            email=email,
            group_id=1
        )
        db_user.password = password
        db.add(db_user)
        await db.commit()
        return db_user
    return _db_user