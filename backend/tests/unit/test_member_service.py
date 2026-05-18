"""Unit tests for MemberService."""

import uuid
from unittest.mock import AsyncMock

import pytest

from app.db.models.member import Member
from app.exceptions import DuplicateEmail, MemberNotFound
from app.services.member_service import MemberService


@pytest.fixture
def mock_repo() -> AsyncMock:
    """Create a mock MemberRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def member_service(mock_repo: AsyncMock) -> MemberService:
    """Create a MemberService instance with mock repo."""
    return MemberService(mock_repo)


@pytest.mark.asyncio
async def test_register_member_success(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test successful member registration."""
    member_id = uuid.uuid4()
    mock_member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    mock_repo.get_by_email.return_value = None
    mock_repo.create.return_value = mock_member

    result = await member_service.register_member(
        name="John Doe", email="john@example.com", phone="555-1234"
    )

    assert result == mock_member
    mock_repo.get_by_email.assert_called_once_with("john@example.com")
    mock_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_register_member_duplicate_email(
    member_service: MemberService,
    mock_repo: AsyncMock,
) -> None:
    """Test member registration with duplicate email raises DuplicateEmail."""
    existing_member = Member(
        id=uuid.uuid4(),
        name="Existing User",
        email="john@example.com",
        phone="555-0000",
        is_active=True,
    )
    mock_repo.get_by_email.return_value = existing_member

    with pytest.raises(DuplicateEmail):
        await member_service.register_member(
            name="New User", email="john@example.com", phone="555-1234"
        )

    mock_repo.get_by_email.assert_called_once_with("john@example.com")
    mock_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_get_member_success(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test successful member retrieval."""
    member_id = uuid.uuid4()
    mock_member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    mock_repo.get.return_value = mock_member

    result = await member_service.get_member(member_id)

    assert result == mock_member
    mock_repo.get.assert_called_once_with(member_id)


@pytest.mark.asyncio
async def test_get_member_not_found(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test member retrieval with non-existent ID raises MemberNotFound."""
    mock_repo.get.return_value = None

    with pytest.raises(MemberNotFound):
        await member_service.get_member(uuid.uuid4())

    mock_repo.get.assert_called_once()


@pytest.mark.asyncio
async def test_list_members(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test listing members with pagination."""
    member1 = Member(
        id=uuid.uuid4(),
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    member2 = Member(
        id=uuid.uuid4(),
        name="Jane Smith",
        email="jane@example.com",
        phone="555-5678",
        is_active=True,
    )
    mock_repo.get_many.return_value = [member1, member2]

    members, next_cursor = await member_service.list_members(limit=20)

    assert len(members) == 2
    assert next_cursor is None
    mock_repo.get_many.assert_called_once()


@pytest.mark.asyncio
async def test_list_members_with_cursor(
    member_service: MemberService,
    mock_repo: AsyncMock,
) -> None:
    """Test listing members with cursor pagination returns next cursor."""
    members = [
        Member(
            id=uuid.uuid4(),
            name=f"Member {i}",
            email=f"member{i}@example.com",
            phone="555-0000",
            is_active=True,
        )
        for i in range(21)
    ]
    mock_repo.get_many.return_value = members

    members_result, next_cursor = await member_service.list_members(limit=20)

    assert len(members_result) == 20
    assert next_cursor == members[20].id


@pytest.mark.asyncio
async def test_update_member_success(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test successful member update."""
    member_id = uuid.uuid4()
    existing_member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    updated_member = Member(
        id=member_id,
        name="John Smith",
        email="john.smith@example.com",
        phone="555-9999",
        is_active=True,
    )
    mock_repo.get.return_value = existing_member
    mock_repo.get_by_email.return_value = None
    mock_repo.update.return_value = updated_member

    result = await member_service.update_member(
        member_id, name="John Smith", email="john.smith@example.com", phone="555-9999"
    )

    assert result == updated_member
    mock_repo.get.assert_called_once_with(member_id)
    mock_repo.update.assert_called_once()


@pytest.mark.asyncio
async def test_update_member_not_found(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test updating non-existent member raises MemberNotFound."""
    mock_repo.get.return_value = None

    with pytest.raises(MemberNotFound):
        await member_service.update_member(uuid.uuid4(), name="New Name")

    mock_repo.get.assert_called_once()
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_member_duplicate_email(
    member_service: MemberService,
    mock_repo: AsyncMock,
) -> None:
    """Test updating member with duplicate email raises DuplicateEmail."""
    member_id = uuid.uuid4()
    existing_member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    other_member = Member(
        id=uuid.uuid4(),
        name="Jane Smith",
        email="jane@example.com",
        phone="555-5678",
        is_active=True,
    )
    mock_repo.get.return_value = existing_member
    mock_repo.get_by_email.return_value = other_member

    with pytest.raises(DuplicateEmail):
        await member_service.update_member(member_id, email="jane@example.com")

    mock_repo.get.assert_called_once_with(member_id)
    mock_repo.get_by_email.assert_called_once_with("jane@example.com")
    mock_repo.update.assert_not_called()


@pytest.mark.asyncio
async def test_update_member_partial(member_service: MemberService, mock_repo: AsyncMock) -> None:
    """Test updating member with partial data."""
    member_id = uuid.uuid4()
    existing_member = Member(
        id=member_id,
        name="John Doe",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    updated_member = Member(
        id=member_id,
        name="John Smith",
        email="john@example.com",
        phone="555-1234",
        is_active=True,
    )
    mock_repo.get.return_value = existing_member
    mock_repo.update.return_value = updated_member

    result = await member_service.update_member(member_id, name="John Smith")

    assert result == updated_member
    mock_repo.get.assert_called_once_with(member_id)
    mock_repo.update.assert_called_once()
