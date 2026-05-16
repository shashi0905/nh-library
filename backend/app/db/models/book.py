"""Book ORM model."""

import uuid

from sqlalchemy import Index, Integer, String
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Book(Base):
    """Represents a book in the library catalogue."""

    __tablename__ = "books"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    author: Mapped[str] = mapped_column(String(255), nullable=False)
    total_copies: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1"
    )
    available: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    # Populated by a DB trigger; not written by the ORM directly.
    search_vector: Mapped[str | None] = mapped_column(TSVECTOR, nullable=True)

    __table_args__ = (Index("ix_books_search_vector", "search_vector", postgresql_using="gin"),)
