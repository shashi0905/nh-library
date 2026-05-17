"""Shared pytest fixtures for unit and integration tests."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from testcontainers.postgres import PostgresContainer

import app.db.models  # noqa: F401
from app.db.base import Base
from app.main import app


@pytest.fixture(scope="session")
def pg_container() -> Generator[PostgresContainer, None, None]:
    """Spin up a postgres:16-alpine container once for the test session."""
    with PostgresContainer("postgres:16-alpine") as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(pg_container: PostgresContainer) -> str:
    """Return the asyncpg connection URL for the test container."""
    return pg_container.get_connection_url().replace("psycopg2", "asyncpg")


@pytest_asyncio.fixture
async def db_engine(db_url: str) -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh async engine per test and apply schema."""
    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(db_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional session that rolls back after each test."""
    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    async with factory() as sess, sess.begin():
        yield sess
        await sess.rollback()


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Yield an async HTTP client for testing the FastAPI application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

