"""SQLAlchemy async engine, session factory, and declarative base."""

from collections.abc import AsyncGenerator
from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.config import settings


engine = create_async_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine,
    expire_on_commit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an AsyncSession; used as a FastAPI dependency."""
    async with AsyncSessionFactory() as session:
        yield session


class Base(DeclarativeBase):
    """Shared declarative base with audit timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=lambda: datetime.now(datetime.UTC),
        nullable=False,
    )
