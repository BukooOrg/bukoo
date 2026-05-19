from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import NotificationEntity


@dataclass(frozen=True)
class NotificationFilters:
    user_id: str | None = None
    is_read: bool | None = None


class INotificationRepository(ABC):
    @abstractmethod
    async def save(self, notification: NotificationEntity) -> None:
        pass

    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: NotificationFilters
    ) -> PaginatedResult[NotificationEntity]:
        pass

    @abstractmethod
    async def find_by_id(self, notification_id: str) -> NotificationEntity | None:
        pass

    @abstractmethod
    async def count_unread(self, user_id: str) -> int:
        pass
