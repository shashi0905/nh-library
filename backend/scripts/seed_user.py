"""Script to create a test staff user in the database."""

import asyncio
import sys
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from passlib.context import CryptContext  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

from app.config import settings  # noqa: E402
from app.db.models.user import User, UserRole  # noqa: E402

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


async def create_staff_user() -> None:
    """Create a staff user in the database."""
    # Create async engine
    engine = create_async_engine(settings.database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if user already exists
        from sqlalchemy import select

        result = await session.execute(select(User).where(User.email == "staff@example.com"))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User staff@example.com already exists with ID: {existing_user.id}")
            return

        # Create new staff user
        hashed_password = hash_password("staff123")
        user = User(
            email="staff@example.com",
            hashed_password=hashed_password,
            role=UserRole.STAFF,
        )

        session.add(user)
        await session.commit()
        await session.refresh(user)

        print("Created staff user:")
        print(f"  Email: {user.email}")
        print(f"  Role: {user.role}")
        print(f"  ID: {user.id}")
        print("\nYou can now login with:")
        print("  Email: staff@example.com")
        print("  Password: staff123")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_staff_user())
