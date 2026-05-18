"""Unit tests for LoanService."""

import datetime as dt
import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import Result

from app.db.models.book import Book
from app.db.models.loan import Loan, LoanStatus
from app.db.models.member import Member
from app.exceptions import (
    BookNotAvailable,
    BookNotFound,
    LoanAlreadyReturned,
    LoanNotFound,
    MemberInactive,
)
from app.services.loan_service import LoanService


@pytest.fixture
def mock_loan_repo() -> AsyncMock:
    """Create a mock LoanRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_db() -> AsyncMock:
    """Create a mock database session."""
    db = AsyncMock()
    return db


@pytest.fixture
def loan_service(mock_loan_repo: AsyncMock, mock_db: AsyncMock) -> LoanService:
    """Create a LoanService instance with mock repo and db."""
    return LoanService(mock_loan_repo, mock_db)


@pytest.mark.asyncio
async def test_borrow_book_success(
    loan_service: LoanService,
    mock_loan_repo: AsyncMock,
    mock_db: AsyncMock,
) -> None:
    """Test successful book borrowing."""
    book_id = uuid.uuid4()
    member_id = uuid.uuid4()
    loan_id = uuid.uuid4()

    book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=5,
    )

    member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )

    loan = Loan(
        id=loan_id,
        book_id=book_id,
        member_id=member_id,
        borrowed_at=dt.datetime.now(dt.UTC),
        due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=14),
        status=LoanStatus.ACTIVE,
    )

    # Mock the SELECT FOR UPDATE query
    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = book
    mock_db.execute.return_value = mock_result
    mock_db.get.return_value = member
    mock_loan_repo.create.return_value = loan

    result = await loan_service.borrow_book(book_id, member_id)

    assert result == loan
    assert book.available == 4  # Should be decremented
    mock_db.flush.assert_called()


@pytest.mark.asyncio
async def test_borrow_book_not_found(loan_service: LoanService, mock_db: AsyncMock) -> None:
    """Test borrowing non-existent book raises BookNotFound."""
    book_id = uuid.uuid4()
    member_id = uuid.uuid4()

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    with pytest.raises(BookNotFound):
        await loan_service.borrow_book(book_id, member_id)


@pytest.mark.asyncio
async def test_borrow_book_not_available(loan_service: LoanService, mock_db: AsyncMock) -> None:
    """Test borrowing book with no available copies raises BookNotAvailable."""
    book_id = uuid.uuid4()
    member_id = uuid.uuid4()

    book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=0,
    )

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = book
    mock_db.execute.return_value = mock_result

    with pytest.raises(BookNotAvailable):
        await loan_service.borrow_book(book_id, member_id)


@pytest.mark.asyncio
async def test_borrow_book_inactive_member(loan_service: LoanService, mock_db: AsyncMock) -> None:
    """Test borrowing with inactive member raises MemberInactive."""
    book_id = uuid.uuid4()
    member_id = uuid.uuid4()

    book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=5,
    )

    member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=False,
    )

    mock_result = MagicMock(spec=Result)
    mock_result.scalar_one_or_none.return_value = book
    mock_db.execute.return_value = mock_result
    mock_db.get.return_value = member

    with pytest.raises(MemberInactive):
        await loan_service.borrow_book(book_id, member_id)


@pytest.mark.asyncio
async def test_return_book_success(
    loan_service: LoanService,
    mock_loan_repo: AsyncMock,
    mock_db: AsyncMock,
) -> None:
    """Test successful book return without fine."""
    loan_id = uuid.uuid4()
    book_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=book_id,
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=10),
        due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=4),
        status=LoanStatus.ACTIVE,
    )

    book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=4,
    )

    mock_loan_repo.get.return_value = loan
    mock_db.get.return_value = book

    # Mock update to return updated loan
    updated_loan = Loan(
        id=loan_id,
        book_id=book_id,
        member_id=loan.member_id,
        borrowed_at=loan.borrowed_at,
        due_date=loan.due_date,
        status=LoanStatus.RETURNED,
        returned_at=dt.datetime.now(dt.UTC),
        fine_amount=None,
        fine_paid=None,
    )
    mock_loan_repo.update.return_value = updated_loan

    result = await loan_service.return_book(loan_id)

    assert result.status == LoanStatus.RETURNED
    assert result.returned_at is not None
    assert result.fine_amount is None
    assert book.available == 5  # Should be incremented


@pytest.mark.asyncio
async def test_return_book_with_fine(
    loan_service: LoanService,
    mock_loan_repo: AsyncMock,
    mock_db: AsyncMock,
) -> None:
    """Test returning overdue book calculates fine."""
    loan_id = uuid.uuid4()
    book_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=book_id,
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=20),
        due_date=dt.datetime.now(dt.UTC) - dt.timedelta(days=6),
        status=LoanStatus.ACTIVE,
    )

    book = Book(
        id=book_id,
        isbn="9780134685991",
        title="Effective Python",
        author="Brett Slatkin",
        total_copies=5,
        available=4,
    )

    mock_loan_repo.get.return_value = loan
    mock_db.get.return_value = book

    # Mock update to return updated loan with fine
    updated_loan = Loan(
        id=loan_id,
        book_id=book_id,
        member_id=loan.member_id,
        borrowed_at=loan.borrowed_at,
        due_date=loan.due_date,
        status=LoanStatus.RETURNED,
        returned_at=dt.datetime.now(dt.UTC),
        fine_amount=Decimal("6.00"),
        fine_paid=None,
    )
    mock_loan_repo.update.return_value = updated_loan

    result = await loan_service.return_book(loan_id)

    assert result.status == LoanStatus.RETURNED
    assert result.returned_at is not None
    assert result.fine_amount is not None
    assert result.fine_amount == Decimal("6.00")  # 6 days overdue * $1.00/day


@pytest.mark.asyncio
async def test_return_book_not_found(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test returning non-existent loan raises LoanNotFound."""
    mock_loan_repo.get.return_value = None

    with pytest.raises(LoanNotFound):
        await loan_service.return_book(uuid.uuid4())


@pytest.mark.asyncio
async def test_return_book_already_returned(
    loan_service: LoanService,
    mock_loan_repo: AsyncMock,
) -> None:
    """Test returning already returned loan raises LoanAlreadyReturned."""
    loan_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=20),
        due_date=dt.datetime.now(dt.UTC) - dt.timedelta(days=6),
        returned_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=5),
        status=LoanStatus.RETURNED,
    )

    mock_loan_repo.get.return_value = loan

    with pytest.raises(LoanAlreadyReturned):
        await loan_service.return_book(loan_id)


@pytest.mark.asyncio
async def test_get_loan_success(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test successful loan retrieval."""
    loan_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC),
        due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=14),
        status=LoanStatus.ACTIVE,
    )

    mock_loan_repo.get.return_value = loan

    result = await loan_service.get_loan(loan_id)

    assert result == loan


@pytest.mark.asyncio
async def test_get_loan_not_found(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test retrieving non-existent loan raises LoanNotFound."""
    mock_loan_repo.get.return_value = None

    with pytest.raises(LoanNotFound):
        await loan_service.get_loan(uuid.uuid4())


@pytest.mark.asyncio
async def test_list_loans(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test listing loans with pagination."""
    loans = [
        Loan(
            id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            borrowed_at=dt.datetime.now(dt.UTC),
            due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=14),
            status=LoanStatus.ACTIVE,
        )
        for _ in range(2)
    ]

    mock_loan_repo.get_many.return_value = loans

    result, next_cursor = await loan_service.list_loans(limit=20)

    assert len(result) == 2
    assert next_cursor is None


@pytest.mark.asyncio
async def test_list_loans_with_cursor(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test listing loans with cursor pagination returns next cursor."""
    loans = [
        Loan(
            id=uuid.uuid4(),
            book_id=uuid.uuid4(),
            member_id=uuid.uuid4(),
            borrowed_at=dt.datetime.now(dt.UTC),
            due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=14),
            status=LoanStatus.ACTIVE,
        )
        for _ in range(21)
    ]

    mock_loan_repo.get_many.return_value = loans

    result, next_cursor = await loan_service.list_loans(limit=20)

    assert len(result) == 20
    assert next_cursor == loans[20].id


@pytest.mark.asyncio
async def test_list_loans_with_filters(
    loan_service: LoanService,
    mock_loan_repo: AsyncMock,
) -> None:
    """Test listing loans with member and status filters."""
    member_id = uuid.uuid4()
    mock_loan_repo.get_many.return_value = []

    await loan_service.list_loans(member_id=member_id, status="ACTIVE")

    mock_loan_repo.get_many.assert_called_once()
    call_kwargs = mock_loan_repo.get_many.call_args.kwargs
    assert call_kwargs["filters"]["member_id"] == member_id
    assert call_kwargs["filters"]["status"] == "ACTIVE"


@pytest.mark.asyncio
async def test_list_loans_overdue(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test listing overdue loans."""
    mock_loan_repo.get_many.return_value = []

    await loan_service.list_loans(overdue=True)

    mock_loan_repo.get_many.assert_called_once()
    call_kwargs = mock_loan_repo.get_many.call_args.kwargs
    assert call_kwargs["filters"]["overdue"] is True


@pytest.mark.asyncio
async def test_pay_fine_success(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test successful fine payment."""
    loan_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=20),
        due_date=dt.datetime.now(dt.UTC) - dt.timedelta(days=6),
        returned_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=5),
        status=LoanStatus.RETURNED,
        fine_amount=Decimal("6.00"),
        fine_paid=False,
    )

    mock_loan_repo.get.return_value = loan

    # Mock update to return updated loan with fine_paid=True
    updated_loan = Loan(
        id=loan_id,
        book_id=loan.book_id,
        member_id=loan.member_id,
        borrowed_at=loan.borrowed_at,
        due_date=loan.due_date,
        returned_at=loan.returned_at,
        status=loan.status,
        fine_amount=loan.fine_amount,
        fine_paid=True,
    )
    mock_loan_repo.update.return_value = updated_loan

    result = await loan_service.pay_fine(loan_id)

    assert result.fine_paid is True


@pytest.mark.asyncio
async def test_pay_fine_no_fine(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test paying fine when no fine exists returns loan unchanged."""
    loan_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC),
        due_date=dt.datetime.now(dt.UTC) + dt.timedelta(days=14),
        status=LoanStatus.ACTIVE,
        fine_amount=None,
        fine_paid=False,
    )

    mock_loan_repo.get.return_value = loan

    result = await loan_service.pay_fine(loan_id)

    assert result == loan
    mock_loan_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_pay_fine_already_paid(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test paying fine when already paid returns loan unchanged."""
    loan_id = uuid.uuid4()

    loan = Loan(
        id=loan_id,
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        borrowed_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=20),
        due_date=dt.datetime.now(dt.UTC) - dt.timedelta(days=6),
        returned_at=dt.datetime.now(dt.UTC) - dt.timedelta(days=5),
        status=LoanStatus.RETURNED,
        fine_amount=Decimal("6.00"),
        fine_paid=True,
    )

    mock_loan_repo.get.return_value = loan

    result = await loan_service.pay_fine(loan_id)

    assert result == loan
    mock_loan_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_pay_fine_not_found(loan_service: LoanService, mock_loan_repo: AsyncMock) -> None:
    """Test paying fine for non-existent loan raises LoanNotFound."""
    mock_loan_repo.get.return_value = None

    with pytest.raises(LoanNotFound):
        await loan_service.pay_fine(uuid.uuid4())
