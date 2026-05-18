"""Loans API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_staff
from app.auth.jwt import TokenData
from app.exceptions import (
    BookNotAvailable,
    BookNotFound,
    LoanAlreadyReturned,
    LoanNotFound,
    MemberInactive,
)
from app.repositories.loan_repo import LoanRepository
from app.schemas.loan import (
    LoanCreate,
    LoanListResponse,
    LoanPayFineRequest,
    LoanResponse,
    LoanReturnRequest,
)
from app.services.loan_service import LoanService

router = APIRouter(prefix="/loans", tags=["loans"])


@router.post("/", response_model=LoanResponse, status_code=status.HTTP_201_CREATED)
async def borrow_book(
    loan: LoanCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> LoanResponse:
    """Borrow a book for a member."""
    loan_repo = LoanRepository(db)
    service = LoanService(loan_repo, db)

    try:
        created = await service.borrow_book(loan.book_id, loan.member_id)
        await db.commit()
        return LoanResponse.model_validate(created)
    except BookNotFound:
        raise HTTPException(status_code=404, detail="Book not found") from None
    except BookNotAvailable:
        raise HTTPException(status_code=409, detail="Book is not available") from None
    except MemberInactive:
        raise HTTPException(status_code=403, detail="Member is inactive") from None


@router.patch("/{loan_id}/return", response_model=LoanResponse)
async def return_book(
    loan_id: uuid.UUID,
    _: LoanReturnRequest,
    db: AsyncSession = Depends(get_db),
    __: TokenData = Depends(require_staff),
) -> LoanResponse:
    """Return a borrowed book."""
    loan_repo = LoanRepository(db)
    service = LoanService(loan_repo, db)

    try:
        returned = await service.return_book(loan_id)
        await db.commit()
        return LoanResponse.model_validate(returned)
    except LoanNotFound as err:
        raise HTTPException(status_code=404, detail="Loan not found") from err
    except LoanAlreadyReturned as err:
        raise HTTPException(status_code=409, detail="Loan already returned") from err


@router.get("/", response_model=LoanListResponse)
async def list_loans(
    member_id: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    overdue: Annotated[bool, Query()] = False,
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    db: AsyncSession = Depends(get_db),
) -> LoanListResponse:
    """List loans with optional filters and pagination."""
    loan_repo = LoanRepository(db)
    service = LoanService(loan_repo, db)

    cursor_uuid = None
    if cursor:
        try:
            cursor_uuid = uuid.UUID(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor") from None

    member_uuid = None
    if member_id:
        try:
            member_uuid = uuid.UUID(member_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid member_id") from None

    loans, next_cursor = await service.list_loans(
        member_id=member_uuid,
        status=status_filter,
        overdue=overdue,
        cursor=cursor_uuid,
        limit=limit,
    )
    return LoanListResponse(
        items=[LoanResponse.model_validate(loan) for loan in loans],
        next_cursor=next_cursor,
    )


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> LoanResponse:
    """Get a loan by ID."""
    loan_repo = LoanRepository(db)
    service = LoanService(loan_repo, db)

    try:
        loan = await service.get_loan(loan_id)
        return LoanResponse.model_validate(loan)
    except LoanNotFound:
        raise HTTPException(status_code=404, detail="Loan not found") from None


@router.post("/{loan_id}/pay-fine", response_model=LoanResponse)
async def pay_fine(
    loan_id: uuid.UUID,
    _: LoanPayFineRequest,
    db: AsyncSession = Depends(get_db),
    __: TokenData = Depends(require_staff),
) -> LoanResponse:
    """Mark a loan fine as paid."""
    loan_repo = LoanRepository(db)
    service = LoanService(loan_repo, db)

    try:
        updated = await service.pay_fine(loan_id)
        await db.commit()
        return LoanResponse.model_validate(updated)
    except LoanNotFound:
        raise HTTPException(status_code=404, detail="Loan not found") from None
