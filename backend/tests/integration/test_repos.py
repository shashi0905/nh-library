"""Integration tests for repository CRUD against a real PostgreSQL container."""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.loan import LoanStatus
from app.repositories.book_repo import BookRepository
from app.repositories.loan_repo import LoanRepository
from app.repositories.member_repo import MemberRepository


@pytest.mark.asyncio
async def test_book_create_and_get(session: AsyncSession) -> None:
    """Created book should be retrievable by id."""
    repo = BookRepository(session)
    book = await repo.create(
        {"id": uuid.uuid4(), "isbn": "9780000000001", "title": "Clean Code", "author": "Martin"}
    )
    fetched = await repo.get(book.id)
    assert fetched is not None
    assert fetched.isbn == "9780000000001"


@pytest.mark.asyncio
async def test_book_update(session: AsyncSession) -> None:
    """Updating a book field should persist the change."""
    repo = BookRepository(session)
    book = await repo.create(
        {"id": uuid.uuid4(), "isbn": "9780000000002", "title": "Old Title", "author": "Author"}
    )
    updated = await repo.update(book.id, {"title": "New Title"})
    assert updated is not None
    assert updated.title == "New Title"


@pytest.mark.asyncio
async def test_book_delete(session: AsyncSession) -> None:
    """Deleted book should not be retrievable."""
    repo = BookRepository(session)
    book = await repo.create(
        {"id": uuid.uuid4(), "isbn": "9780000000003", "title": "To Delete", "author": "Author"}
    )
    deleted = await repo.delete(book.id)
    assert deleted is True
    assert await repo.get(book.id) is None


@pytest.mark.asyncio
async def test_book_get_not_found(session: AsyncSession) -> None:
    """get() should return None for a non-existent id."""
    repo = BookRepository(session)
    assert await repo.get(uuid.uuid4()) is None


@pytest.mark.asyncio
async def test_member_create_and_get_by_email(session: AsyncSession) -> None:
    """Member should be findable by email after creation."""
    repo = MemberRepository(session)
    member = await repo.create(
        {"id": uuid.uuid4(), "name": "Alice", "email": "alice@example.com"}
    )
    found = await repo.get_by_email("alice@example.com")
    assert found is not None
    assert found.id == member.id


@pytest.mark.asyncio
async def test_member_soft_delete(session: AsyncSession) -> None:
    """Deleting a member should set is_active=False, not remove the row."""
    repo = MemberRepository(session)
    member = await repo.create(
        {"id": uuid.uuid4(), "name": "Bob", "email": "bob@example.com"}
    )
    await repo.delete(member.id)
    fetched = await repo.get(member.id)
    assert fetched is not None
    assert fetched.is_active is False


@pytest.mark.asyncio
async def test_loan_create_and_list(session: AsyncSession) -> None:
    """Created loan should appear in list filtered by member_id."""
    book_repo = BookRepository(session)
    member_repo = MemberRepository(session)
    loan_repo = LoanRepository(session)

    book = await book_repo.create(
        {"id": uuid.uuid4(), "isbn": "9780000000004", "title": "Book", "author": "Author"}
    )
    member = await member_repo.create(
        {"id": uuid.uuid4(), "name": "Carol", "email": "carol@example.com"}
    )
    loan = await loan_repo.create(
        {
            "id": uuid.uuid4(),
            "book_id": book.id,
            "member_id": member.id,
            "due_date": datetime.now(timezone.utc) + timedelta(days=14),
        }
    )
    loans = await loan_repo.list(filters={"member_id": member.id})
    assert any(l.id == loan.id for l in loans)


@pytest.mark.asyncio
async def test_loan_status_update(session: AsyncSession) -> None:
    """Loan status should update to RETURNED."""
    book_repo = BookRepository(session)
    member_repo = MemberRepository(session)
    loan_repo = LoanRepository(session)

    book = await book_repo.create(
        {"id": uuid.uuid4(), "isbn": "9780000000005", "title": "Book2", "author": "Author"}
    )
    member = await member_repo.create(
        {"id": uuid.uuid4(), "name": "Dave", "email": "dave@example.com"}
    )
    loan = await loan_repo.create(
        {
            "id": uuid.uuid4(),
            "book_id": book.id,
            "member_id": member.id,
            "due_date": datetime.now(timezone.utc) + timedelta(days=14),
        }
    )
    updated = await loan_repo.update(
        loan.id,
        {"status": LoanStatus.RETURNED, "returned_at": datetime.now(timezone.utc)},
    )
    assert updated is not None
    assert updated.status == LoanStatus.RETURNED
