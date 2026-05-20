"""
Shared async DB session context manager for Celery tasks.

Each asyncio.run() call creates a new event loop. The DatabaseManager singleton
binds its asyncpg pool to the first loop it runs on, so reusing it across
asyncio.run() invocations produces cross-loop errors. Creating a fresh engine
per task invocation (and disposing it in finally) is the correct pattern.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_configs


@asynccontextmanager
async def task_db_session() -> AsyncGenerator[AsyncSession, None]:
    configs = get_configs()
    engine = create_async_engine(
        f"{configs.POSTGRES_ASYNC_PREFIX}{configs.POSTGRES_URI}",
        pool_pre_ping=True,
        echo=configs.APP_DEBUG,
    )
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
