"""Shared pytest fixtures for unit and integration tests."""

import os
from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

import app.db.models  # noqa: F401
from app.api.deps import get_db
from app.db.base import Base
from app.main import app


@pytest_asyncio.fixture(scope="session")
async def db_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create a fresh async engine per test session and apply schema using CI postgres."""
    # Explicitly use test_db to avoid any config.py defaults
    db_url = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/test_db",
    )
    # Ensure we're using test_db, not library
    if "library" in db_url:
        db_url = db_url.replace("/library", "/test_db")
    engine = create_async_engine(db_url, pool_pre_ping=True)
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
    async with factory() as sess:
        yield sess
        # Rollback any changes made during the test
        await sess.rollback()


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncGenerator[AsyncClient, None]:
    """Yield an async HTTP client for testing the FastAPI application with test DB."""

    # Create a test-specific session factory
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        factory = async_sessionmaker(db_engine, expire_on_commit=False)
        async with factory() as session:
            yield session

    # Override the FastAPI dependency to use test database
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        yield async_client

    # Clean up: remove the override
    app.dependency_overrides.clear()
