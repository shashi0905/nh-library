"""User repository — SQLAlchemy async implementation."""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.user import User
from app.repositories.base import IRepository


class UserRepository(IRepository[User]):
    """Concrete repository for User entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> User | None:
        """Return User by primary key."""
        return await self._session.get(User, id)

    async def get_by_email(self, email: str) -> User | None:
        """Return User by email."""
        result = await self._session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_many(
        self,
        filters: dict[str, Any] | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[User]:
        """Return users with optional filters and cursor pagination."""
        stmt = select(User)
        if filters and (role := filters.get("role")):
            stmt = stmt.where(User.role == role)
        if cursor:
            stmt = stmt.where(User.id > cursor)
        stmt = stmt.order_by(User.id).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> User:
        """Insert a new User."""
        user = User(**data)
        self._session.add(user)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> User | None:
        """Update User fields; return updated User or None."""
        user = await self.get(id)
        if user is None:
            return None
        for key, value in data.items():
            setattr(user, key, value)
        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def delete(self, id: uuid.UUID) -> bool:
        """Hard-delete a User record."""
        user = await self.get(id)
        if user is None:
            return False
        await self._session.delete(user)
        await self._session.flush()
        return True
