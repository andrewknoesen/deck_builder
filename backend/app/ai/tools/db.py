from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.db import engine

# ADK calls tool functions directly — there's no FastAPI request/route cycle,
# so tool code can't use Depends(get_db) or app.dependency_overrides the way
# routes do. This is a separate, directly-importable session factory for tool
# code; tests patch get_tool_session itself (not dependency_overrides) to
# point it at a test engine.
ToolSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession,
)


def get_tool_session() -> AsyncSession:
    return ToolSessionLocal()
