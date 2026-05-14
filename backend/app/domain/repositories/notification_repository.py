from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities import NotificationEntity


class INotificationRepository(ABC):
    @abstractmethod
    async def save(self, notification: NotificationEntity) -> None:
        pass
