"""SQLite connection setup (async, via SQLAlchemy + aiosqlite)."""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""


class AsyncSessionEngine:
    """Lazily-created async engine + session factory, rebuilt on demand.

    Wrapped in a small class (rather than bare module-level globals) so
    tests can point `settings.database_url` at a tmp file and get a fresh
    engine/sessionmaker without leaking connections across test runs.
    """

    def __init__(self) -> None:
        self.engine = create_async_engine(settings.database_url, echo=False)
        self.session_factory = async_sessionmaker(self.engine, expire_on_commit=False)

    async def init_models(self) -> None:
        """Create all tables declared on `Base` if they don't exist yet."""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


_engine_holder = AsyncSessionEngine()


def get_engine_holder() -> AsyncSessionEngine:
    """Return the current engine holder (module-level singleton)."""
    return _engine_holder


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding an AsyncSession bound to the current engine."""
    async with _engine_holder.session_factory() as session:
        yield session
