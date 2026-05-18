"""Member service — business logic for members."""

import uuid

from app.db.models.member import Member
from app.exceptions import DuplicateEmail, MemberNotFound
from app.repositories.member_repo import MemberRepository


class MemberService:
    """Service layer for member operations."""

    def __init__(self, repo: MemberRepository) -> None:
        """Initialize with a MemberRepository instance."""
        self._repo = repo

    async def register_member(self, name: str, email: str, phone: str | None = None) -> Member:
        """Register a new member."""
        # Check for duplicate email
        existing = await self._repo.get_by_email(email)
        if existing is not None:
            raise DuplicateEmail()

        return await self._repo.create(
            {"name": name, "email": email, "phone": phone, "is_active": True}
        )

    async def get_member(self, member_id: uuid.UUID) -> Member:
        """Get a member by ID."""
        member = await self._repo.get(member_id)
        if member is None:
            raise MemberNotFound()
        return member

    async def list_members(
        self, cursor: uuid.UUID | None = None, limit: int = 20
    ) -> tuple[list[Member], uuid.UUID | None]:
        """List members with pagination."""
        filters = {"active_only": True}
        members = await self._repo.get_many(filters=filters, cursor=cursor, limit=limit + 1)

        next_cursor = None
        if len(members) > limit:
            next_cursor = members[limit].id
            members = members[:limit]

        return members, next_cursor

    async def update_member(
        self,
        member_id: uuid.UUID,
        name: str | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> Member:
        """Update a member."""
        member = await self._repo.get(member_id)
        if member is None:
            raise MemberNotFound()

        # Check for duplicate email if updating
        if email is not None and email != member.email:
            existing = await self._repo.get_by_email(email)
            if existing is not None:
                raise DuplicateEmail()

        data = {}
        if name is not None:
            data["name"] = name
        if email is not None:
            data["email"] = email
        if phone is not None:
            data["phone"] = phone

        updated = await self._repo.update(member_id, data)
        if updated is None:
            raise MemberNotFound()
        return updated
