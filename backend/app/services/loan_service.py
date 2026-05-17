"""Loan service — business logic for loans."""

import datetime as dt
import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
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
from app.repositories.loan_repo import LoanRepository


class LoanService:
    """Service layer for loan operations."""

    def __init__(self, loan_repo: LoanRepository, db: AsyncSession) -> None:
        """Initialize with LoanRepository and database session."""
        self._loan_repo = loan_repo
        self._db = db

    async def borrow_book(self, book_id: uuid.UUID, member_id: uuid.UUID) -> Loan:
        """Borrow a book for a member using SELECT FOR UPDATE to prevent race conditions."""
        # Use SELECT FOR UPDATE to lock the book row and prevent concurrent borrows
        stmt = select(Book).where(Book.id == book_id).with_for_update()
        result = await self._db.execute(stmt)
        book = result.scalar_one_or_none()

        if book is None:
            raise BookNotFound()

        if book.available <= 0:
            raise BookNotAvailable()

        # Check member is active
        member = await self._db.get(Member, member_id)
        if member is None:
            raise BookNotFound()  # Reuse BookNotFound for member not found to avoid leaking info
        if not member.is_active:
            raise MemberInactive()

        # Create loan
        due_date = dt.datetime.now(dt.UTC) + dt.timedelta(days=settings.loan_duration_days)
        loan = await self._loan_repo.create(
            {
                "book_id": book_id,
                "member_id": member_id,
                "due_date": due_date,
                "status": LoanStatus.ACTIVE,
            }
        )

        # Decrement available copies
        book.available -= 1
        await self._db.flush()

        return loan

    async def return_book(self, loan_id: uuid.UUID) -> Loan:
        """Return a borrowed book and compute fine if overdue."""
        loan = await self._loan_repo.get(loan_id)
        if loan is None:
            raise LoanNotFound()

        if loan.status == LoanStatus.RETURNED:
            raise LoanAlreadyReturned()

        # Calculate fine if overdue
        fine_amount = None
        if dt.datetime.now(dt.UTC) > loan.due_date:
            overdue_days = (dt.datetime.now(dt.UTC) - loan.due_date).days
            fine_amount = Decimal(overdue_days) * Decimal(str(settings.fine_rate_per_day))

        # Update loan
        updated = await self._loan_repo.update(
            loan_id,
            {
                "status": LoanStatus.RETURNED,
                "returned_at": dt.datetime.now(dt.UTC),
                "fine_amount": fine_amount,
            },
        )

        if updated is None:
            raise LoanNotFound()

        # Increment available copies
        book = await self._db.get(Book, loan.book_id)
        if book:
            book.available += 1
            await self._db.flush()

        return updated

    async def get_loan(self, loan_id: uuid.UUID) -> Loan:
        """Get a loan by ID."""
        loan = await self._loan_repo.get(loan_id)
        if loan is None:
            raise LoanNotFound()
        return loan

    async def list_loans(
        self,
        member_id: uuid.UUID | None = None,
        status: str | None = None,
        overdue: bool = False,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> tuple[list[Loan], uuid.UUID | None]:
        """List loans with optional filters and pagination."""
        filters: dict[str, uuid.UUID | str | bool] = {}
        if member_id:
            filters["member_id"] = member_id
        if status:
            filters["status"] = status
        if overdue:
            filters["overdue"] = True

        loans = await self._loan_repo.get_many(filters=filters, cursor=cursor, limit=limit + 1)

        next_cursor = None
        if len(loans) > limit:
            next_cursor = loans[limit].id
            loans = loans[:limit]

        return loans, next_cursor

    async def pay_fine(self, loan_id: uuid.UUID) -> Loan:
        """Mark a loan fine as paid."""
        loan = await self._loan_repo.get(loan_id)
        if loan is None:
            raise LoanNotFound()

        if not loan.fine_amount or loan.fine_paid:
            # No fine to pay or already paid - just return the loan
            return loan

        updated = await self._loan_repo.update(loan_id, {"fine_paid": True})
        if updated is None:
            raise LoanNotFound()

        return updated
