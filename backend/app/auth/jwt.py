"""JWT authentication utilities."""

from datetime import UTC, datetime, timedelta

import jwt
from jwt import exceptions as jwt_exceptions
from pydantic import BaseModel

from app.config import settings


class TokenData(BaseModel):
    """JWT token payload."""

    sub: str  # user email
    role: str  # user role


def create_access_token(email: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode: dict[str, str | int] = {"sub": email, "role": role}
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire_mins = settings.access_token_expire_minutes
        expire = datetime.now(UTC) + timedelta(minutes=expire_mins)
    to_encode["exp"] = int(expire.timestamp())
    encoded_jwt: str = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email = payload.get("sub")
        role = payload.get("role")
        if not email or not role:
            raise ValueError("Invalid token payload")
        token_data = TokenData(sub=email, role=role)
        return token_data
    except jwt_exceptions.InvalidTokenError as e:
        raise ValueError(f"Invalid token: {e}") from e
