"""Book repository — SQLAlchemy async implementation."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.book import Book
from app.repositories.base import IRepository


class BookRepository(IRepository[Book]):
    """Concrete repository for Book entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> Book | None:
        """Return Book by primary key."""
        return await self._session.get(Book, id)

    async def get_by_isbn(self, isbn: str) -> Book | None:
        """Return Book by ISBN."""
        result = await self._session.execute(select(Book).where(Book.isbn == isbn))
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[Book]:
        """Return books with optional filters and cursor pagination."""
        stmt = select(Book)
        if filters:
            if filters.get("available_only"):
                stmt = stmt.where(Book.available > 0)
            if q := filters.get("q"):
                stmt = stmt.where(
                    Book.search_vector.op("@@")(
                        Book.search_vector.op("to_tsquery")(q)  # type: ignore[attr-defined]
                    )
                )
        if cursor:
            stmt = stmt.where(Book.id > cursor)
        stmt = stmt.order_by(Book.id).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def search(self, query: str, limit: int = 20) -> list[Book]:
        """Full-text search on title + author via tsvector."""
        stmt = (
            select(Book)
            .where(
                Book.search_vector.op("@@")(  # type: ignore[attr-defined]
                    Book.search_vector.op("plainto_tsquery")(query)
                )
            )
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> Book:
        """Insert a new Book."""
        book = Book(**data)
        self._session.add(book)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> Book | None:
        """Update Book fields; return updated Book or None."""
        book = await self.get(id)
        if book is None:
            return None
        for key, value in data.items():
            setattr(book, key, value)
        await self._session.flush()
        await self._session.refresh(book)
        return book

    async def delete(self, id: uuid.UUID) -> bool:
        """Delete Book by id."""
        book = await self.get(id)
        if book is None:
            return False
        await self._session.delete(book)
        await self._session.flush()
        return True
