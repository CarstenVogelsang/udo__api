"""
Async SQLAlchemy database setup for SQLite.
"""
from typing import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.models.geo import Base
# Import all models to ensure they are registered with Base.metadata
from app.models import base  # noqa: F401
from app.models import etl  # noqa: F401
from app.models import com  # noqa: F401
from app.models import smart_filter  # noqa: F401
from app.models import setting  # noqa: F401

settings = get_settings()

# Ensure data directory exists
data_dir = Path(__file__).parent.parent / "data"
data_dir.mkdir(exist_ok=True)

# Async Engine for SQLite
# Using StaticPool for SQLite to handle concurrent access
engine = create_async_engine(
    settings.sqlite_database_url,
    echo=settings.debug,
    future=True,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Session Factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    """Creates all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drops all tables from the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for FastAPI endpoints.
    Yields an async database session.
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
