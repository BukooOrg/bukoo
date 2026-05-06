from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_configs


class DatabaseManager:
    _instance: DatabaseManager | None = None

    def __init__(self) -> None:
        if DatabaseManager._instance is not None:
            raise RuntimeError("Use DatabaseManager.get_instance() instead.")

        configs = get_configs()
        assert configs.POSTGRES_URI, "POSTGRES_URI must be configured."

        # todo: move configs to appropriate location
        self.engine: AsyncEngine = create_async_engine(
            f"{configs.POSTGRES_ASYNC_PREFIX}{configs.POSTGRES_URI}",
            pool_size=10,
            max_overflow=20,
            echo=configs.APP_DEBUG,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    @classmethod
    def get_instance(cls) -> DatabaseManager:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession, None]:
    db_manager = DatabaseManager.get_instance()
    async with db_manager.session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with session_scope() as session:
        yield session
