"""Member request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class MemberCreate(BaseModel):
    """Request schema for creating a member."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    name: str
    email: EmailStr
    phone: str | None = None


class MemberUpdate(BaseModel):
    """Request schema for updating a member."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None


class MemberResponse(BaseModel):
    """Response schema for a single member."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    phone: str | None
    joined_at: datetime
    is_active: bool
    created_at: datetime
    updated_at: datetime


class MemberListResponse(BaseModel):
    """Response schema for a list of members."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    items: list[MemberResponse]
    next_cursor: uuid.UUID | None
