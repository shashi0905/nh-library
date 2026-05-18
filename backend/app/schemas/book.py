"""Book request and response schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator


class BookCreate(BaseModel):
    """Request schema for creating a book."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    isbn: str
    title: str
    author: str
    total_copies: int = 1

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str) -> str:
        """Validate ISBN-13 format (13 digits)."""
        if not v.isdigit() or len(v) != 13:
            msg = "ISBN must be 13 digits"
            raise ValueError(msg)
        # Simple check digit validation for ISBN-13
        total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(v[:12]))
        check_digit = (10 - (total % 10)) % 10
        if int(v[12]) != check_digit:
            msg = "Invalid ISBN-13 check digit"
            raise ValueError(msg)
        return v

    @field_validator("total_copies")
    @classmethod
    def validate_total_copies(cls, v: int) -> int:
        """Validate total_copies is positive."""
        if v <= 0:
            msg = "total_copies must be greater than 0"
            raise ValueError(msg)
        return v


class BookUpdate(BaseModel):
    """Request schema for updating a book."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    isbn: str | None = None
    title: str | None = None
    author: str | None = None
    total_copies: int | None = None

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        """Validate ISBN-13 format if provided."""
        if v is None:
            return v
        if not v.isdigit() or len(v) != 13:
            msg = "ISBN must be 13 digits"
            raise ValueError(msg)
        total = sum(int(digit) * (1 if i % 2 == 0 else 3) for i, digit in enumerate(v[:12]))
        check_digit = (10 - (total % 10)) % 10
        if int(v[12]) != check_digit:
            msg = "Invalid ISBN-13 check digit"
            raise ValueError(msg)
        return v

    @field_validator("total_copies")
    @classmethod
    def validate_total_copies(cls, v: int | None) -> int | None:
        """Validate total_copies is positive if provided."""
        if v is None:
            return v
        if v <= 0:
            msg = "total_copies must be greater than 0"
            raise ValueError(msg)
        return v


class BookResponse(BaseModel):
    """Response schema for a single book."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    id: uuid.UUID
    isbn: str
    title: str
    author: str
    total_copies: int
    available: int
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    """Response schema for a list of books."""

    model_config = ConfigDict(strict=True, from_attributes=True)

    items: list[BookResponse]
    next_cursor: uuid.UUID | None
