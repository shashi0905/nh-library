"""Integration tests for Loans API."""

import asyncio
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
async def test_list_loans_empty(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing loans when none exist."""
    response = await client.get(
        "/api/v1/loans",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_borrow_book(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test borrowing a book."""
    # Create a book
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    # Create a member
    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Borrow the book
    loan_data = {"book_id": str(book_id), "member_id": str(member_id)}
    response = await client.post(
        "/api/v1/loans",
        json=loan_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["book_id"] == str(book_id)
    assert data["member_id"] == str(member_id)
    assert data["status"] == "ACTIVE"
    assert "id" in data


@pytest.mark.asyncio
async def test_borrow_book_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test borrowing a non-existent book returns 404."""
    # Create a member
    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Try to borrow non-existent book
    loan_data = {"book_id": str(uuid.uuid4()), "member_id": str(member_id)}
    response = await client.post(
        "/api/v1/loans",
        json=loan_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_borrow_book_not_available(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test borrowing a book with no available copies returns 409."""
    # Create a book with 1 copy
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 1,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    # Create a member
    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Borrow the book (uses the only copy)
    await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Try to borrow again (no copies available)
    loan_data = {"book_id": str(book_id), "member_id": str(member_id)}
    response = await client.post(
        "/api/v1/loans",
        json=loan_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_borrow_book_inactive_member(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test borrowing with inactive member returns 403."""
    # Create a book
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    # Create a member
    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Deactivate the member (manually update in DB)
    from app.db.models.member import Member

    member = await session.get(Member, uuid.UUID(member_id))
    member.is_active = False
    await session.flush()

    # Try to borrow with inactive member
    loan_data = {"book_id": str(book_id), "member_id": str(member_id)}
    response = await client.post(
        "/api/v1/loans",
        json=loan_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_return_book(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test returning a borrowed book."""
    # Create a book and member
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Borrow the book
    loan_response = await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    loan_id = loan_response.json()["id"]

    # Return the book
    response = await client.patch(
        f"/api/v1/loans/{loan_id}/return",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RETURNED"
    assert data["returned_at"] is not None


@pytest.mark.asyncio
async def test_return_book_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test returning a non-existent loan returns 404."""
    response = await client.patch(
        f"/api/v1/loans/{uuid.uuid4()}/return",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_return_book_already_returned(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test returning an already returned book returns 409."""
    # Create a book and member
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Borrow and return the book
    loan_response = await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    loan_id = loan_response.json()["id"]

    await client.patch(
        f"/api/v1/loans/{loan_id}/return",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Try to return again
    response = await client.patch(
        f"/api/v1/loans/{loan_id}/return",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_loan(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test getting a loan by ID."""
    # Create a book, member, and loan
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    loan_response = await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    loan_id = loan_response.json()["id"]

    # Get the loan
    response = await client.get(f"/api/v1/loans/{loan_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == loan_id
    assert data["book_id"] == str(book_id)


@pytest.mark.asyncio
async def test_get_loan_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test getting a non-existent loan returns 404."""
    response = await client.get(f"/api/v1/loans/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_loans_with_filters(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing loans with member and status filters."""
    # Create a book and member
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Create a loan
    await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # List loans for the member
    response = await client.get(
        f"/api/v1/loans?member_id={member_id}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 1
    assert all(loan["member_id"] == str(member_id) for loan in data["items"])


@pytest.mark.asyncio
async def test_list_loans_with_pagination(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing loans with pagination."""
    # Create a book and member
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 50,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Create multiple loans
    for _ in range(25):
        await client.post(
            "/api/v1/loans",
            json={"book_id": str(book_id), "member_id": str(member_id)},
            headers={"Authorization": f"Bearer {staff_token}"},
        )

    # List loans with limit
    response = await client.get(
        "/api/v1/loans?limit=20",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_pay_fine(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test paying a fine."""
    # Create a book and member
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 5,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Create a loan
    loan_response = await client.post(
        "/api/v1/loans",
        json={"book_id": str(book_id), "member_id": str(member_id)},
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    loan_id = loan_response.json()["id"]

    # Manually set a fine on the loan
    from decimal import Decimal

    from app.db.models.loan import Loan

    loan = await session.get(Loan, uuid.UUID(loan_id))
    loan.fine_amount = Decimal("5.00")
    loan.status = "RETURNED"
    await session.flush()

    # Pay the fine
    response = await client.post(
        f"/api/v1/loans/{loan_id}/pay-fine",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["fine_paid"] is True


@pytest.mark.asyncio
async def test_pay_fine_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test paying fine for non-existent loan returns 404."""
    response = await client.post(
        f"/api/v1/loans/{uuid.uuid4()}/pay-fine",
        json={},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_borrow_book_requires_auth(session: AsyncSession, client: AsyncClient) -> None:
    """Test borrowing a book without authentication returns 401."""
    response = await client.post(
        "/api/v1/loans",
        json={"book_id": str(uuid.uuid4()), "member_id": str(uuid.uuid4())},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_concurrent_borrow_race_condition(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test concurrent borrow requests prevent race condition using SELECT FOR UPDATE."""
    # Create a book with only 1 copy
    book_response = await client.post(
        "/api/v1/books",
        json={
            "isbn": "9780134685991",
            "title": "Effective Python",
            "author": "Brett Slatkin",
            "total_copies": 1,
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    book_id = book_response.json()["id"]

    # Create a member
    member_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = member_response.json()["id"]

    # Attempt concurrent borrows
    async def borrow_attempt() -> None:
        return await client.post(
            "/api/v1/loans",
            json={"book_id": str(book_id), "member_id": str(member_id)},
            headers={"Authorization": f"Bearer {staff_token}"},
        )

    # Fire 5 concurrent borrow requests
    results = await asyncio.gather(*[borrow_attempt() for _ in range(5)])

    # Only one should succeed (201), others should fail (409)
    success_count = sum(1 for r in results if r.status_code == 201)
    conflict_count = sum(1 for r in results if r.status_code == 409)

    assert success_count == 1, f"Expected 1 successful borrow, got {success_count}"
    assert conflict_count == 4, f"Expected 4 conflicts, got {conflict_count}"
