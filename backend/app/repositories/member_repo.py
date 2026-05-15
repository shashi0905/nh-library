"""Member repository — SQLAlchemy async implementation."""

from typing import Any
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.member import Member
from app.repositories.base import IRepository


class MemberRepository(IRepository[Member]):
    """Concrete repository for Member entities."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, id: uuid.UUID) -> Member | None:
        """Return Member by primary key."""
        return await self._session.get(Member, id)

    async def get_by_email(self, email: str) -> Member | None:
        """Return Member by email address."""
        result = await self._session.execute(select(Member).where(Member.email == email))
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: dict[str, Any] | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[Member]:
        """Return members with optional cursor pagination."""
        stmt = select(Member)
        if filters and filters.get("active_only"):
            stmt = stmt.where(Member.is_active.is_(True))
        if cursor:
            stmt = stmt.where(Member.id > cursor)
        stmt = stmt.order_by(Member.id).limit(limit)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, data: dict[str, Any]) -> Member:
        """Insert a new Member."""
        member = Member(**data)
        self._session.add(member)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> Member | None:
        """Update Member fields; return updated Member or None."""
        member = await self.get(id)
        if member is None:
            return None
        for key, value in data.items():
            setattr(member, key, value)
        await self._session.flush()
        await self._session.refresh(member)
        return member

    async def delete(self, id: uuid.UUID) -> bool:
        """Soft-delete by deactivating the member."""
        member = await self.get(id)
        if member is None:
            return False
        member.is_active = False
        await self._session.flush()
        return True
