"""Shared pytest fixtures for unit and integration tests."""

import asyncio
from collections.abc import AsyncGenerator, Generator

import app.db.models  # noqa: F401
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

from app.db.base import Base


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Single event loop for the entire test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def pg_container() -> Generator[PostgresContainer, None, None]:
    """Spin up a postgres:16-alpine container for the test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest_asyncio.fixture(scope="session")
async def db_engine(pg_container: PostgresContainer) -> AsyncGenerator[AsyncEngine, None]:
    """Create async engine pointed at the test container and run migrations."""
    url = pg_container.get_connection_url().replace("psycopg2", "asyncpg")
    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session that rolls back after each test for isolation."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as sess, sess.begin():
        yield sess
        await sess.rollback()
