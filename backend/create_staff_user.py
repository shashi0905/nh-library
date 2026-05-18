# First, run the migration to create the users table
# alembic upgrade head

# Then create a staff user via Python script or directly in the database
# Using Python:
import asyncio

from passlib.context import CryptContext

from app.db.base import engine
from app.db.models.user import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_user() -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    async_session = async_sessionmaker(engine, expire_on_commit=False)
    async with async_session() as session, session.begin():
        user = User(
            email="staff@example.com",
            hashed_password=pwd_context.hash("staff123"),
            role="STAFF",
        )
        session.add(user)
        await session.flush()


asyncio.run(create_user())
