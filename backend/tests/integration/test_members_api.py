"""Integration tests for Members API."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import create_access_token
from app.db.models.user import UserRole


@pytest.fixture
def staff_token() -> str:
    """Create a staff JWT token for testing."""
    return create_access_token(email="staff@example.com", role=UserRole.STAFF.value)


@pytest.mark.asyncio
async def test_list_members_empty(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing members when none exist."""
    response = await client.get(
        "/api/v1/members",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["next_cursor"] is None


@pytest.mark.asyncio
async def test_register_member(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test registering a new member."""
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
    }

    response = await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "John Doe"
    assert data["email"] == "john@example.com"
    assert data["phone"] == "555-1234"
    assert data["is_active"] is True
    assert "id" in data


@pytest.mark.asyncio
async def test_register_member_duplicate_email(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test registering a member with duplicate email returns 409."""
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
    }

    # First registration
    await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Second registration with same email
    response = await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_member(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test getting a member by ID."""
    # First register a member
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
    }

    create_response = await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = create_response.json()["id"]

    # Get the member
    response = await client.get(f"/api/v1/members/{member_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == member_id
    assert data["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_get_member_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test getting a non-existent member returns 404."""
    response = await client.get(f"/api/v1/members/{uuid.uuid4()}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_member(session: AsyncSession, staff_token: str, client: AsyncClient) -> None:
    """Test updating a member."""
    # First register a member
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
    }

    create_response = await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = create_response.json()["id"]

    # Update the member
    update_data = {"name": "John Smith", "phone": "555-9999"}
    response = await client.patch(
        f"/api/v1/members/{member_id}",
        json=update_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "John Smith"
    assert data["phone"] == "555-9999"
    assert data["email"] == "john@example.com"  # Unchanged


@pytest.mark.asyncio
async def test_update_member_not_found(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test updating a non-existent member returns 404."""
    response = await client.patch(
        f"/api/v1/members/{uuid.uuid4()}",
        json={"name": "New Name"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_member_duplicate_email(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test updating member with duplicate email returns 409."""
    # Register two members
    member1_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member1_id = member1_response.json()["id"]

    await client.post(
        "/api/v1/members",
        json={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": "555-5678",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    # Try to update member1 with member2's email
    response = await client.patch(
        f"/api/v1/members/{member1_id}",
        json={"email": "jane@example.com"},
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_members_with_pagination(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing members with pagination."""
    # Create multiple members
    for i in range(25):
        await client.post(
            "/api/v1/members",
            json={
                "name": f"Member {i}",
                "email": f"member{i}@example.com",
                "phone": "555-0000",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )

    # List members with limit
    response = await client.get(
        "/api/v1/members?limit=20",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["next_cursor"] is not None


@pytest.mark.asyncio
async def test_list_members_with_cursor(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test listing members with cursor pagination."""
    # Create members
    for i in range(25):
        await client.post(
            "/api/v1/members",
            json={
                "name": f"Member {i}",
                "email": f"member{i}@example.com",
                "phone": "555-0000",
            },
            headers={"Authorization": f"Bearer {staff_token}"},
        )

    # Get first page
    first_response = await client.get(
        "/api/v1/members?limit=20",
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    first_data = first_response.json()
    next_cursor = first_data["next_cursor"]

    # Get second page with cursor
    second_response = await client.get(
        f"/api/v1/members?limit=20&cursor={next_cursor}",
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert second_response.status_code == 200
    second_data = second_response.json()
    assert len(second_data["items"]) == 5  # Remaining 5 members
    assert second_data["next_cursor"] is None


@pytest.mark.asyncio
async def test_register_member_requires_auth(session: AsyncSession, client: AsyncClient) -> None:
    """Test registering a member without authentication returns 401."""
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "555-1234",
    }

    response = await client.post("/api/v1/members", json=member_data)

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_update_member_requires_auth(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test updating a member without authentication returns 401."""
    # Create a member first
    create_response = await client.post(
        "/api/v1/members",
        json={
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "555-1234",
        },
        headers={"Authorization": f"Bearer {staff_token}"},
    )
    member_id = create_response.json()["id"]

    # Try to update without auth
    response = await client.patch(
        f"/api/v1/members/{member_id}",
        json={"name": "New Name"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_member_without_phone(
    session: AsyncSession, staff_token: str, client: AsyncClient
) -> None:
    """Test registering a member without optional phone field."""
    member_data = {
        "name": "John Doe",
        "email": "john@example.com",
    }

    response = await client.post(
        "/api/v1/members",
        json=member_data,
        headers={"Authorization": f"Bearer {staff_token}"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["phone"] is None
