from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


_engine: AsyncEngine | None = None
_Session: async_sessionmaker[AsyncSession] | None = None
_initialized: bool = False


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().DATABASE_URL, echo=False, future=True)
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _Session
    if _Session is None:
        _Session = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _Session


async def init_db() -> None:
    from .models import Post  # noqa: F401

    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    global _initialized
    _initialized = True


async def ensure_db_initialized() -> None:
    global _initialized
    if not _initialized:
        await init_db()
