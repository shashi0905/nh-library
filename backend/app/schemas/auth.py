"""Authentication schemas."""

from pydantic import BaseModel, EmailStr, Field


class TokenRequest(BaseModel):
    """Request schema for login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response schema for token."""

    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh."""

    refresh_token: str = Field(..., min_length=1)
