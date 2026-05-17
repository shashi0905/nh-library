"""Cursor-based pagination utilities."""

import base64
import uuid
from datetime import datetime


def encode_cursor(created_at: datetime, id: uuid.UUID) -> str:
    """Encode a cursor from created_at and id as base64."""
    combined = f"{created_at.isoformat()}:{id}"
    return base64.b64encode(combined.encode()).decode()


def decode_cursor(cursor: str) -> tuple[datetime, uuid.UUID]:
    """Decode a base64 cursor back to created_at and id."""
    decoded = base64.b64decode(cursor.encode()).decode()
    created_at_str, id_str = decoded.split(":")
    created_at = datetime.fromisoformat(created_at_str)
    id = uuid.UUID(id_str)
    return created_at, id
