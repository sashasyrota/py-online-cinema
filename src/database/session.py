import os
from pathlib import Path
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine, select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine, AsyncEngine
from sqlalchemy.orm import sessionmaker, Session

from src.database.models.base import Base
from src.database.models import Payment
from src.config import settings


BASE_DIR: Path = Path(__file__).parent.parent

#POSTGRES
ASYNC_DATABASE_URL = (
    f"postgresql+asyncpg://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
)

async_engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


SYNC_DATABASE_URL = (
    f"postgresql+psycopg2://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@"
    f"{settings.POSTGRES_HOST}:{settings.POSTGRES_DB_PORT}/{settings.POSTGRES_DB}"
)

sync_engine = create_engine(SYNC_DATABASE_URL, echo=False)

SyncSessionLocal = sessionmaker(bind=sync_engine, autoflush=False, autocommit=False)

def get_sync_db() -> Session:
    with SyncSessionLocal() as session:
        yield session

#SQLITE
SQLITE_DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'cinema.db')}"

sqlite_async_engine = create_async_engine(SQLITE_DATABASE_URL, echo=False)

AsyncSqliteSessionLocal = async_sessionmaker(
    bind=sqlite_async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)

async def get_sqlite_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSqliteSessionLocal() as session:
        yield session


async def reset_sqlite_database() -> None:
    """
    Reset the SQLite database.

    This function drops all existing tables and recreates them.
    It is useful for testing purposes or when resetting the database is required.

    Warning: This action is irreversible and will delete all stored data.

    :return: None
    """
    async with sqlite_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
