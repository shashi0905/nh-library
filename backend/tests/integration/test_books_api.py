"""Integration tests for Books API."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.db.models.user import UserRole


@pytest.fixture
def staff_token() -> str:
    """Create a staff JWT token for testing."""
    return create_access_token(email="staff@example.com", role=UserRole.STAFF.value)


@pytest.mark.asyncio
async def test_list_books_empty(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing books when none exist."""
    response = await client.get(
        "/api/v1/books/",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_create_book(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test creating a new book."""
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == "9780134685991"
    assert data["title"] == "Effective Python"
    assert data["author"] == "Brett Slatkin"
    assert data["total_copies"] == 5
    assert data["available"] == 5
    assert "id" in data


@pytest.mark.asyncio
async def test_create_book_duplicate_isbn(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test creating a book with duplicate ISBN returns 409."""
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    # First creation
    await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Second creation with same ISBN
    response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_book_invalid_isbn(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test creating a book with invalid ISBN returns 422."""
    book_data = {
        "isbn": "123",  # Invalid ISBN (not 13 digits)
        "title": "Test Book",
        "author": "Test Author",
        "total_copies": 1,
    }

    response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_get_book(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test getting a book by ID."""
    # First create a book
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    create_response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = create_response.json()["id"]

    # Get the book
    response = await client.get(f"/api/v1/books/{book_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == book_id
    assert data["isbn"] == "9780134685991"


@pytest.mark.asyncio
async def test_get_book_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test getting a non-existent book returns 404."""
    response = await client.get(f"/api/v1/books/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_book(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test updating a book."""
    # First create a book
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    create_response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = create_response.json()["id"]

    # Update the book
    update_data = {"title": "Effective Python 2nd Edition"}
    response = await client.patch(
        f"/api/v1/books/{book_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Effective Python 2nd Edition"
    assert data["isbn"] == "9780134685991"  # Unchanged


@pytest.mark.asyncio
async def test_update_book_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test updating a non-existent book returns 404."""
    response = await client.patch(
        f"/api/v1/books/{uuid.uuid4()}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_deactivate_book(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test deactivating a book."""
    # First create a book
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    create_response = await client.post(
        "/api/v1/books/",
        json=book_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = create_response.json()["id"]

    # Deactivate the book
    response = await client.delete(
        f"/api/v1/books/{book_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 204

    # Verify book is deactivated
    get_response = await client.get(f"/api/v1/books/{book_id}")

    assert get_response.json()["available"] == 0


@pytest.mark.asyncio
async def test_deactivate_book_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test deactivating a non-existent book returns 404."""
    response = await client.delete(
        f"/api/v1/books/{uuid.uuid4()}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_books_with_pagination(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing books with pagination."""
    # Create multiple books
    for i in range(25):
        await client.post(
            "/api/v1/books/",
            json={
                "isbn": f"97801346859{i:02d}",
                "title": f"Book {i}",
                "author": "Author",
                "total_copies": 1,
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )

    # List books with limit
    response = await client.get(
        "/api/v1/books/?limit=20",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_list_books_with_search(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing books with search query."""
    # Create books
    await client.post(
        "/api/v1/books/",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 1,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    await client.post(
        "/api/v1/books/",
        json={
            "isbn": "9780132350884",
            "title": "Clean Code",
            "author": "Robert Martin",
            "total_copies": 1,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Search for "Python"
    response = await client.get(
        "/api/v1/books/?q=python",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    # Note: Full-text search depends on PostgreSQL tsvector, which may not work in tests


@pytest.mark.asyncio
async def test_list_books_available_only(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing only available books."""
    # Create a book with available copies
    await client.post(
        "/api/v1/books/",
        json={
            "isbn": "9780134685991",
            "title": "Available Book",
            "author": "Author",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # List available books
    response = await client.get(
        "/api/v1/books/?available_only=true",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert all(book["available"] > 0 for book in data["items"])


@pytest.mark.asyncio
async def test_create_book_requires_auth(session: AsyncSession, client: AsyncClient) -> None:
    """Test creating a book without authentication returns 401."""
    book_data = {
        "isbn": "9780134685991",
        "title": "Effective Python",
        "author": "Brett Slatkin",
        "total_copies": 5,
    }

    response = await client.post("/api/v1/books/", json=book_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_book_requires_auth(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test updating a book without authentication returns 401."""
    # Create a book first
    create_response = await client.post(
        "/api/v1/books/",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = create_response.json()["id"]

    # Try to update without auth
    response = await client.patch(
        f"/api/v1/books/{book_id}",
        json={"title": "New Title"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_delete_book_requires_auth(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test deleting a book without authentication returns 401."""
    # Create a book first
    create_response = await client.post(
        "/api/v1/books/",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = create_response.json()["id"]

    # Try to delete without auth
    response = await client.delete(f"/api/v1/books/{book_id}")

    assert response.status_code == 401
