"""Loan request and response schemas."""

import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.db.models.loan import LoanStatus


class LoanCreate(BaseModel):
    """Request schema for creating (borrowing) a loan."""

    model_config = ConfigDict(from_attributes=True)

    book_id: uuid.UUID
    member_id: uuid.UUID


class LoanReturnRequest(BaseModel):
    """Request schema for returning a book."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    pass  # No additional fields needed for return


class LoanPayFineRequest(BaseModel):
    """Request schema for paying a fine."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    pass  # No additional fields needed for pay fine


class LoanResponse(BaseModel):
    """Response schema for a single loan."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    id: uuid.UUID
    book_id: uuid.UUID
    member_id: uuid.UUID
    borrowed_at: datetime
    due_date: datetime
    returned_at: datetime | None
    status: LoanStatus
    fine_amount: Decimal | None
    fine_paid: bool
    created_at: datetime


class LoanListResponse(BaseModel):
    """Response schema for a list of loans."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    items: list[LoanResponse]
    next_cursor: uuid.UUID | None
