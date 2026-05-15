"""Unit tests for ORM model instantiation and defaults."""

import uuid
from datetime import datetime

from app.db.models.book import Book
from app.db.models.loan import Loan, LoanStatus
from app.db.models.member import Member


def test_book_defaults() -> None:
    """Book should default total_copies and available to 1."""
    book = Book(isbn="9780000000001", title="Test", author="Author")
    assert book.total_copies == 1
    assert book.available == 1


def test_member_defaults() -> None:
    """Member should default is_active to True."""
    member = Member(name="Alice", email="alice@example.com")
    assert member.is_active is True


def test_loan_defaults() -> None:
    """Loan should default status to ACTIVE and fine_paid to False."""
    loan = Loan(
        book_id=uuid.uuid4(),
        member_id=uuid.uuid4(),
        due_date=datetime.now(datetime.UTC),
    )
    assert loan.status == LoanStatus.ACTIVE
    assert loan.fine_paid is False


def test_loan_status_enum_values() -> None:
    """LoanStatus enum must have exactly the three expected values."""
    assert set(LoanStatus) == {LoanStatus.ACTIVE, LoanStatus.RETURNED, LoanStatus.OVERDUE}
