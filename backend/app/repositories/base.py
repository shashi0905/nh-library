"""Abstract repository interface."""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

T = TypeVar("T")


class IRepository(ABC, Generic[T]):
    """Generic async repository contract."""

    @abstractmethod
    async def get(self, id: uuid.UUID) -> T | None:
        """Return entity by primary key, or None if not found."""
        ...

    @abstractmethod
    async def get_many(
        self,
        filters: dict[str, Any] | None = None,
        cursor: uuid.UUID | None = None,
        limit: int = 20,
    ) -> list[T]:
        """Return a page of entities, optionally filtered and cursor-paginated."""
        ...

    @abstractmethod
    async def create(self, data: dict[str, Any]) -> T:
        """Persist a new entity and return it."""
        ...

    @abstractmethod
    async def update(self, id: uuid.UUID, data: dict[str, Any]) -> T | None:
        """Update an existing entity; return updated entity or None if not found."""
        ...

    @abstractmethod
    async def delete(self, id: uuid.UUID) -> bool:
        """Delete entity by id; return True if deleted, False if not found."""
        ...
