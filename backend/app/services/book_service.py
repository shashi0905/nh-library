"""Book service — business logic for books."""

import uuid

from app.db.models.book import Book
from app.exceptions import BookNotFound, DuplicateISBN
from app.repositories.book_repo import BookRepository


class BookService:
    """Service layer for book operations."""

    def __init__(self, repo: BookRepository) -> None:
        """Initialize with a BookRepository instance."""
        self._repo = repo

    async def create_book(self, isbn: str, title: str, author: str, total_copies: int = 1) -> Book:
        """Create a new book."""
        # Check for duplicate ISBN
        existing = await self._repo.get_by_isbn(isbn)
        if existing is not None:
            raise DuplicateISBN()

        return await self._repo.create(
            {
                "isbn": isbn,
                "title": title,
                "author": author,
                "total_copies": total_copies,
                "available": total_copies,
            }
        )

    async def get_book(self, book_id: uuid.UUID) -> Book:
        """Get a book by ID."""
        book = await self._repo.get(book_id)
        if book is None:
            raise BookNotFound()
        return book

    async def list_books(
        self,
        query: str | None = None,
        available_only: bool = False,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[Book], uuid.UUID | None]:
        """List books with optional search and pagination."""
        filters: dict[str, bool | str] = {}
        if query:
            filters["q"] = query
        if available_only:
            filters["available_only"] = True

        books = await self._repo.get_many(filters=filters, cursor=cursor, limit=limit + 1)

        next_cursor = None
        if len(books) > limit:
            next_cursor = books[limit].id
            books = books[:limit]

        return books, next_cursor

    async def update_book(
        self,
        book_id: uuid.UUID,
        isbn: str | None = None,
        title: str | None = None,
        author: str | None = None,
        total_copies: int | None = None,
    ) -> Book:
        """Update a book."""
        book = await self._repo.get(book_id)
        if book is None:
            raise BookNotFound()

        # Check for duplicate ISBN if updating
        if isbn is not None and isbn != book.isbn:
            existing = await self._repo.get_by_isbn(isbn)
            if existing is not None:
                raise DuplicateISBN()

        data: dict[str, str | int] = {}
        if isbn is not None:
            data["isbn"] = isbn
        if title is not None:
            data["title"] = title
        if author is not None:
            data["author"] = author
        if total_copies is not None:
            data["total_copies"] = total_copies

        updated = await self._repo.update(book_id, data)
        if updated is None:
            raise BookNotFound()
        return updated

    async def deactivate_book(self, book_id: uuid.UUID) -> Book:
        """Deactivate a book by setting available to 0."""
        book = await self._repo.get(book_id)
        if book is None:
            raise BookNotFound()

        updated = await self._repo.update(book_id, {"available": 0})
        if updated is None:
            raise BookNotFound()
        return updated
