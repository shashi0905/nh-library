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
        """Validate ISBN format (10 or 13 digits)."""
        v = v.strip()
        # Accept ISBN-10 or ISBN-13 format
        if len(v) == 10:
            # ISBN-10 validation (simplified)
            if not v.replace("-", "").replace(" ", "").isdigit():
                msg = "ISBN must contain only digits"
                raise ValueError(msg)
        elif len(v) == 13:
            # ISBN-13 validation
            if not v.isdigit():
                msg = "ISBN-13 must be 13 digits"
                raise ValueError(msg)
        else:
            msg = "ISBN must be 10 or 13 characters"
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
        """Validate ISBN format if provided."""
        if v is None:
            return v
        v = v.strip()
        # Accept ISBN-10 or ISBN-13 format
        if len(v) == 10:
            # ISBN-10 validation (simplified)
            if not v.replace("-", "").replace(" ", "").isdigit():
                msg = "ISBN must contain only digits"
                raise ValueError(msg)
        elif len(v) == 13:
            # ISBN-13 validation
            if not v.isdigit():
                msg = "ISBN-13 must be 13 digits"
                raise ValueError(msg)
        else:
            msg = "ISBN must be 10 or 13 characters"
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
