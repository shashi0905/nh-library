"""API dependencies."""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import TokenData, decode_token
from app.db.base import AsyncSessionFactory
from app.db.models.user import UserRole


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get database session."""
    async with AsyncSessionFactory() as session:
        yield session


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> TokenData:
    """Get current user from Bearer token."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header",
        )

    token = authorization[7:]
    try:
        token_data = decode_token(token)
        return token_data
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        ) from e


async def require_staff(
    current_user: Annotated[TokenData, Depends(get_current_user)],
) -> TokenData:
    """Require user to have STAFF role."""
    if current_user.role != UserRole.STAFF.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return current_user
