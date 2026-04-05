from pathlib import Path
from typing import AsyncGenerator, Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session

from src.config import settings


BASE_DIR: Path = Path(__file__).parent.parent

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
