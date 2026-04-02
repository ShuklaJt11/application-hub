import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.models  # noqa: F401
from app.db.base import Base


def _test_database_url() -> str:
    test_database_url = os.getenv("TEST_DATABASE_URL")
    if not test_database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must be set for tests. Refusing to run against "
            "the application database."
        )

    database_url = os.getenv("DATABASE_URL")
    if database_url and test_database_url == database_url:
        raise RuntimeError(
            "TEST_DATABASE_URL must not be the same as DATABASE_URL. "
            "Tests call drop_all() in teardown."
        )

    return test_database_url


@pytest_asyncio.fixture
async def test_engine() -> AsyncGenerator:
    engine = create_async_engine(_test_database_url(), echo=False, pool_pre_ping=True)

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with session_factory() as session:
        yield session
