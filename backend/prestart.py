
import logging

from app.core.db import engine
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

max_tries = 60 * 5  # 5 minutes
wait_seconds = 1


async def init() -> None:
    try:
        # Try to create session to check if DB is awake
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database is ready! 🚀")
    except Exception as e:
        logger.error(f"Database connection trace: {e}")
        raise e


async def main() -> None:
    logger.info("Initializing service")
    
    # Simple retry loop
    for i in range(max_tries):
        try:
            await init()
            break
        except Exception:
            logger.info(f"Database not ready, waiting {wait_seconds}s...")
            import asyncio
            await asyncio.sleep(wait_seconds)
    else:
        logger.error("Could not connect to database.")
        raise Exception("Database connection failed")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
