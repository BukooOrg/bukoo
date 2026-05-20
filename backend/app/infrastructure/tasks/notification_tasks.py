from __future__ import annotations

import asyncio

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import NotificationEntity
from app.domain.repositories import INotificationRepository
from app.infrastructure.db.repositories.notification_repository_impl import (
    NotificationRepositoryImpl,
)
from app.infrastructure.tasks.celery_app import celery_app
from app.infrastructure.tasks.task_db import task_db_session


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
        async with task_db_session() as session:
            repo: INotificationRepository = NotificationRepositoryImpl(session)
            await _apply_notification_update(
                repo, session, notification_id, success=True
            )

    asyncio.run(_run())


@celery_app.task(name="notification.mark_failed", queue="default")
def mark_notification_failed(notification_id: str) -> None:
    async def _run() -> None:
        async with task_db_session() as session:
            repo: INotificationRepository = NotificationRepositoryImpl(session)
            await _apply_notification_update(
                repo, session, notification_id, success=False
            )

    asyncio.run(_run())
