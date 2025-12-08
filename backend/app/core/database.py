"""Async database utilities.

Provides a minimal SQLAlchemy async engine/session setup so the FastAPI app
can start even when no external database is provisioned. Defaults to a local
SQLite file but can be overridden via ``DATABASE_URL``.
"""

from __future__ import annotations

import os
import logging
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Declarative base for ORM models."""


def _get_default_database_url() -> str:
    # Use file-based SQLite to persist data across runs while keeping defaults lightweight
    return "sqlite+aiosqlite:///./app.db"


DATABASE_URL = os.getenv("DATABASE_URL", _get_default_database_url())

# Lazily created engine/session to avoid import-time side effects
engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    global engine, SessionLocal
    if engine is None:
        connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
        engine = create_async_engine(
            DATABASE_URL,
            future=True,
            echo=False,
            connect_args=connect_args,
        )
        SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
        logger.info("Initialized async engine for %s", DATABASE_URL)
    return engine


async def get_db() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency that yields an async session."""
    if SessionLocal is None:
        get_engine()

    assert SessionLocal is not None  # for type checkers
    async with SessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_models() -> None:
    """Create tables for local development if using SQLite."""
    if not DATABASE_URL.startswith("sqlite"):
        return
    eng = get_engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
