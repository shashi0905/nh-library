"""Unit tests for BookService."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.db.models.book import Book
from app.exceptions import BookNotFound, DuplicateISBN
from app.services.book_service import BookService


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Create a mock BookRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def book_service(mock_repo: AsyncMock) -> BookService:
    """Create a BookService instance with mock repo."""
    return BookService(mock_repo)


@pytest.mark.asyncio
async def test_create_book_success(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test successful book creation."""
    book_id = uuid.uuid4()
    mock_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=5,
    )
    mock_repo.get_by_isbn.return_value = None
    mock_repo.create.return_value = mock_book

    result = await book_service.create_book(
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
    )

    assert result == mock_book
    mock_repo.get_by_isbn.assert_called_once_with("9780134685991")
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test book creation with duplicate ISBN raises DuplicateISBN."""
    existing_book = Book(
        id=uuid.uuid4(),
        isbn="9780134685991",
        title="Existing Book",
        author="Author",
        total_copies=1,
        available=1,
    )
    mock_repo.get_by_isbn.return_value = existing_book

    with pytest.raises(DuplicateISBN):
        await book_service.create_book(
            isbn="9780134685991",
            title="New Book",
            author="Author",
            total_copies=1,
        )

    mock_repo.get_by_isbn.assert_called_once_with("9780134685991")
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_book_success(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test successful book retrieval."""
    book_id = uuid.uuid4()
    mock_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=5,
    )
    mock_repo.get.return_value = mock_book

    result = await book_service.get_book(book_id)

    assert result == mock_book
    mock_repo.get.assert_called_once_with(book_id)


@pytest.mark.asyncio
async def test_get_book_not_found(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test book retrieval with non-existent ID raises BookNotFound."""
    mock_repo.get.return_value = None

    with pytest.raises(BookNotFound):
        await book_service.get_book(uuid.uuid4())

    mock_repo.get.assert_called_once()


@pytest.mark.asyncio
async def test_list_books(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test listing books with pagination."""
    book1 = Book(
        id=uuid.uuid4(),
        isbn="9780134685991",
        title="Book 1",
        author="Author 1",
        total_copies=1,
        available=1,
    )
    book2 = Book(
        id=uuid.uuid4(),
        isbn="9780132350884",
        title="Book 2",
        author="Author 2",
        total_copies=1,
        available=1,
    )
    mock_repo.get_many.return_value = [book1, book2]

    books, next_cursor = await book_service.list_books(limit=20)

    assert len(books) == 2
    assert next_cursor is None
    mock_repo.get_many.assert_called_once()


@pytest.mark.asyncio
async def test_list_books_with_cursor(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test listing books with cursor pagination returns next cursor."""
    books = [
        Book(
            id=uuid.uuid4(),
            isbn=f"978013468599{i}",
            title=f"Book {i}",
            author="Author",
            total_copies=1,
            available=1,
        )
        for i in range(21)
    ]
    mock_repo.get_many.return_value = books

    books_result, next_cursor = await book_service.list_books(limit=20)

    assert len(books_result) == 20
    assert next_cursor == books[20].id


@pytest.mark.asyncio
async def test_list_books_with_search(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test listing books with search query."""
    mock_repo.get_many.return_value = []

    await book_service.list_books(query="python")

    mock_repo.get_many.assert_called_once()
    call_kwargs = mock_repo.get_many.call_args.kwargs
    assert "filters" in call_kwargs
    assert call_kwargs["filters"]["q"] == "python"


@pytest.mark.asyncio
async def test_list_books_available_only(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test listing books with available_only filter."""
    mock_repo.get_many.return_value = []

    await book_service.list_books(available_only=True)

    mock_repo.get_many.assert_called_once()
    call_kwargs = mock_repo.get_many.call_args.kwargs
    assert "filters" in call_kwargs
    assert call_kwargs["filters"]["available_only"] is True


@pytest.mark.asyncio
async def test_update_book_success(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test successful book update."""
    book_id = uuid.uuid4()
    existing_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Old Title",
        author="Old Author",
        total_copies=1,
        available=1,
    )
    updated_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="New Title",
        author="New Author",
        total_copies=5,
        available=5,
    )
    mock_repo.get.return_value = existing_book
    mock_repo.get_by_isbn.return_value = None
    mock_repo.update.return_value = updated_book

    result = await book_service.update_book(
        book_id, title="New Title", author="New Author", total_copies=5
    )

    assert result == updated_book
    mock_repo.get.assert_called_once_with(book_id)
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_book_not_found(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test updating non-existent book raises BookNotFound."""
    mock_repo.get.return_value = None

    with pytest.raises(BookNotFound):
        await book_service.update_book(uuid.uuid4(), title="New Title")

    mock_repo.get.assert_called_once()
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_book_duplicate_isbn(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test updating book with duplicate ISBN raises DuplicateISBN."""
    book_id = uuid.uuid4()
    existing_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Title",
        author="Author",
        total_copies=1,
        available=1,
    )
    other_book = Book(
        id=uuid.uuid4(),
        isbn="9780132350884",
        title="Other Book",
        author="Author",
        total_copies=1,
        available=1,
    )
    mock_repo.get.return_value = existing_book
    mock_repo.get_by_isbn.return_value = other_book

    with pytest.raises(DuplicateISBN):
        await book_service.update_book(book_id, isbn="9780132350884")

    mock_repo.get.assert_called_once_with(book_id)
    mock_repo.get_by_isbn.assert_called_once_with("9780132350884")
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_deactivate_book_success(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test successful book deactivation."""
    book_id = uuid.uuid4()
    existing_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Title",
        author="Author",
        total_copies=5,
        available=5,
    )
    deactivated_book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Title",
        author="Author",
        total_copies=5,
        available=0,
    )
    mock_repo.get.return_value = existing_book
    mock_repo.update.return_value = deactivated_book

    result = await book_service.deactivate_book(book_id)

    assert result == deactivated_book
    assert result.available == 0
    mock_repo.get.assert_called_once_with(book_id)
    mock_repo.update.assert_called_once_with(book_id, {"available": 0})


@pytest.mark.asyncio
async def test_deactivate_book_not_found(book_service: BookService, mock_repo: AsyncMock) -> None:
    """Test deactivating non-existent book raises BookNotFound."""
    mock_repo.get.return_value = None

    with pytest.raises(BookNotFound):
        await book_service.deactivate_book(uuid.uuid4())

    mock_repo.get.assert_called_once()
    mock_repo.update.assert_not_called()
