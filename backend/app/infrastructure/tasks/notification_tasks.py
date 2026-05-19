from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_configs
from app.domain.entities import NotificationEntity
from app.domain.repositories import INotificationRepository
from app.infrastructure.db.repositories.notification_repository_impl import (
    NotificationRepositoryImpl,
)
from app.infrastructure.tasks.celery_app import celery_app


@asynccontextmanager
async def _task_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fresh engine + session per task invocation.

    DatabaseManager singleton binds its asyncpg pool to the first event loop.
    Each asyncio.run() creates a NEW loop, which conflicts with pooled connections
    from a previous loop. Creating a fresh engine here avoids the cross-loop error.
    """
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


async def _apply_notification_update(
    repo: INotificationRepository,
    session: AsyncSession,
    notification_id: str,
    *,
    success: bool,
) -> None:
    notification: NotificationEntity | None = await repo.find_by_id(notification_id)
    if notification is None:
        return
    if success:
        notification.mark_sent()
    else:
        notification.mark_failed()
    await repo.save(notification)
    await session.commit()


@celery_app.task(name="notification.mark_sent", queue="default")
def mark_notification_sent(notification_id: str) -> None:
    async def _run() -> None:
        async with _task_db_session() as session:
            repo: INotificationRepository = NotificationRepositoryImpl(session)
            await _apply_notification_update(
                repo, session, notification_id, success=True
            )

    asyncio.run(_run())


@celery_app.task(name="notification.mark_failed", queue="default")
def mark_notification_failed(notification_id: str) -> None:
    async def _run() -> None:
        async with _task_db_session() as session:
            repo: INotificationRepository = NotificationRepositoryImpl(session)
            await _apply_notification_update(
                repo, session, notification_id, success=False
            )

    asyncio.run(_run())
