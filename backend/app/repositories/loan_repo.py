"""Loan repository — SQLAlchemy async implementation."""

from datetime import datetime
from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.loan import Loan, LoanStatus
from app.repositories.base import IRepository


class LoanRepository(IRepository[Loan]):
    """Concrete repository for Loan entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> Loan | None:
        """Return Loan by primary key."""
        return await self._session.get(Loan, id)

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[Loan]:
        """Return loans with optional filters and cursor pagination."""
        stmt = select(Loan)
        if filters:
            if member_id := filters.get("member_id"):
                stmt = stmt.where(Loan.member_id == member_id)
            if status := filters.get("status"):
                stmt = stmt.where(Loan.status == status)
            if filters.get("overdue"):
                stmt = stmt.where(
                    Loan.status == LoanStatus.ACTIVE,
                    Loan.due_date < datetime.now(datetime.UTC),
                )
        if cursor:
            stmt = stmt.where(Loan.id > cursor)
        stmt = stmt.order_by(Loan.id).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def list_active_overdue(self) -> list[Loan]:
        """Return all ACTIVE loans past their due date (for overdue task)."""
        stmt = select(Loan).where(
            Loan.status == LoanStatus.ACTIVE,
            Loan.due_date < datetime.now(datetime.UTC),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> Loan:
        """Insert a new Loan."""
        loan = Loan(**data)
        self._session.add(loan)
        await self._session.flush()
        await self._session.refresh(loan)
        return loan

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> Loan | None:
        """Update Loan fields; return updated Loan or None."""
        loan = await self.get(id)
        if loan is None:
            return None
        for key, value in data.items():
            setattr(loan, key, value)
        await self._session.flush()
        await self._session.refresh(loan)
        return loan

    async def delete(self, id: uuid.UUID) -> bool:
        """Hard-delete a Loan record."""
        loan = await self.get(id)
        if loan is None:
            return False
        await self._session.delete(loan)
        await self._session.flush()
        return True
