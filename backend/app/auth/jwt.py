"""JWT authentication utilities."""

from datetime import datetime, timedelta

from jose import JWTError, jwt
from pydantic import BaseModel

from app.config import settings


class TokenData(BaseModel):
    """JWT token payload."""

    sub: str  # user email
    role: str  # user role


def create_access_token(email: str, role: str, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token."""
    to_encode = {"sub": email, "role": role}
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": int(expire.timestamp())})  # type: ignore[dict-item]
    encoded_jwt: str = jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        email: str = payload.get("sub")
        role: str = payload.get("role")
        if email is None or role is None:
            raise ValueError("Invalid token payload")
        token_data = TokenData(sub=email, role=role)
        return token_data
    except JWTError as e:
        raise ValueError(f"Invalid token: {e}") from e
