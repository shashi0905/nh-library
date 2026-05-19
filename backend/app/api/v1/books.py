"""Books API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_staff
from app.auth.jwt import TokenData
from app.exceptions import BookNotFound, DuplicateISBN
from app.repositories.book_repo import BookRepository
from app.schemas.book import BookCreate, BookListResponse, BookResponse, BookUpdate
from app.services.book_service import BookService

router = APIRouter(prefix="/books", tags=["books"], redirect_slashes=False)


@router.get("", response_model=BookListResponse)
async def list_books(
    q: Annotated[str | None, Query()] = None,
    available_only: Annotated[bool, Query()] = False,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
    db: AsyncSession = Depends(get_db),
) -> BookListResponse:
    """List books with optional search and pagination."""
    repo = BookRepository(db)
    service = BookService(repo)

    cursor_uuid = None
    if cursor:
        try:
            cursor_uuid = uuid.UUID(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor") from None

    books, next_cursor = await service.list_books(
        query=q, available_only=available_only, cursor=cursor_uuid, limit=limit
    )
    return BookListResponse(
        items=[BookResponse.model_validate(b) for b in books],
        next_cursor=next_cursor,
    )


@router.post("", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    book: BookCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> BookResponse:
    """Create a new book."""
    repo = BookRepository(db)
    service = BookService(repo)

    try:
        created = await service.create_book(
            isbn=book.isbn, title=book.title, author=book.author, total_copies=book.total_copies
        )
        await db.commit()
        return BookResponse.model_validate(created)
    except DuplicateISBN:
        raise HTTPException(status_code=409, detail="ISBN already exists") from None


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> BookResponse:
    """Get a book by ID."""
    repo = BookRepository(db)
    service = BookService(repo)

    try:
        book = await service.get_book(book_id)
        return BookResponse.model_validate(book)
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found") from None


@router.patch("/{book_id}", response_model=BookResponse)
async def update_book(
    book_id: uuid.UUID,
    book: BookUpdate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> BookResponse:
    """Update a book."""
    repo = BookRepository(db)
    service = BookService(repo)

    try:
        updated = await service.update_book(
            book_id,
            isbn=book.isbn,
            title=book.title,
            author=book.author,
            total_copies=book.total_copies,
        )
        await db.commit()
        return BookResponse.model_validate(updated)
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found") from None
    except DuplicateISBN:
        raise HTTPException(status_code=409, detail="ISBN already exists") from None


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_book(
    book_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> None:
    """Deactivate a book."""
    repo = BookRepository(db)
    service = BookService(repo)

    try:
        await service.deactivate_book(book_id)
        await db.commit()
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found") from None
