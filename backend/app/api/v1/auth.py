"""Authentication API router."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.auth.jwt import create_access_token, decode_token
from app.config import settings
from app.repositories.user_repo import UserRepository
from app.schemas.auth import RefreshTokenRequest, TokenRequest, TokenResponse

router = APIRouter(prefix="/auth", tags=["auth"], redirect_slashes=False)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return bool(pwd_context.verify(plain_password, hashed_password))


@router.post("/token", response_model=TokenResponse)
async def login(credentials: TokenRequest, db: AsyncSession = Depends(get_db)) -> TokenResponse:
    """Login and get an access token."""
    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(credentials.email)

    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    access_token = create_access_token(
        email=user.email,
        role=user.role.value,
        expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
    )

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)
) -> TokenResponse:
    """Refresh an access token."""
    try:
        token_data = decode_token(refresh_request.refresh_token)
        user_repo = UserRepository(db)
        user = await user_repo.get_by_email(token_data.sub)

        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )

        access_token = create_access_token(
            email=user.email,
            role=user.role.value,
            expires_delta=timedelta(minutes=settings.access_token_expire_minutes),
        )

        return TokenResponse(access_token=access_token, token_type="bearer")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
        ) from e


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout endpoint (client-side token removal)."""
    return {"message": "Logout successful"}
