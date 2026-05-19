"""Members API router."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, require_staff
from app.auth.jwt import TokenData
from app.exceptions import DuplicateEmail, MemberNotFound
from app.repositories.member_repo import MemberRepository
from app.schemas.member import MemberCreate, MemberListResponse, MemberResponse, MemberUpdate
from app.services.member_service import MemberService

router = APIRouter(prefix="/members", tags=["members"], redirect_slashes=False)


@router.get("", response_model=MemberListResponse)
async def list_members(
    cursor: Annotated[str | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 20,
    db: AsyncSession = Depends(get_db),
) -> MemberListResponse:
    """List active members with pagination."""
    repo = MemberRepository(db)
    service = MemberService(repo)

    cursor_uuid = None
    if cursor:
        try:
            cursor_uuid = uuid.UUID(cursor)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid cursor") from None

    members, next_cursor = await service.list_members(cursor=cursor_uuid, limit=limit)
    return MemberListResponse(
        items=[MemberResponse.model_validate(m) for m in members],
        next_cursor=next_cursor,
    )


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
async def register_member(
    member: MemberCreate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> MemberResponse:
    """Register a new member."""
    repo = MemberRepository(db)
    service = MemberService(repo)

    try:
        created = await service.register_member(
            name=member.name, email=member.email, phone=member.phone
        )
        await db.commit()
        return MemberResponse.model_validate(created)
    except DuplicateEmail:
        raise HTTPException(status_code=409, detail="Email already exists") from None


@router.get("/{member_id}", response_model=MemberResponse)
async def get_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Get a member by ID."""
    repo = MemberRepository(db)
    service = MemberService(repo)

    try:
        member = await service.get_member(member_id)
        return MemberResponse.model_validate(member)
    except MemberNotFound as e:
        raise HTTPException(status_code=404, detail="Member not found") from e


@router.patch("/{member_id}", response_model=MemberResponse)
async def update_member(
    member_id: uuid.UUID,
    member: MemberUpdate,
    db: AsyncSession = Depends(get_db),
    _: TokenData = Depends(require_staff),
) -> MemberResponse:
    """Update a member."""
    repo = MemberRepository(db)
    service = MemberService(repo)

    try:
        updated = await service.update_member(
            member_id, name=member.name, email=member.email, phone=member.phone
        )
        await db.commit()
        return MemberResponse.model_validate(updated)
    except MemberNotFound:
        raise HTTPException(status_code=404, detail="Member not found") from None
    except DuplicateEmail:
        raise HTTPException(status_code=409, detail="Email already exists") from None
