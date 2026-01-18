
import asyncio
import logging

from sqlmodel import select

from app.core.db import AsyncSession, engine
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_initial_data() -> None:
    async with AsyncSession(engine) as session:
        result = await session.execute(select(User).where(User.id == 1))
        user = result.scalar_one_or_none()

        if user:
            logger.info("User with ID 1 already exists")
        else:
            logger.info("Creating default user with ID 1")
            user = User(
                id=1,
                email="admin@example.com",
                full_name="Admin User",
                google_sub="seed_user_sub",
                is_active=True,
            )
            session.add(user)
            await session.commit()
            logger.info("Default user created")


async def main() -> None:
    logger.info("Creating initial data")
    await create_initial_data()
    logger.info("Initial data created")


if __name__ == "__main__":
    asyncio.run(main())
