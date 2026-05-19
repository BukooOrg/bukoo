from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.constants import NotificationStatus


@dataclass
class NotificationEntity:
    """
    Notification has no updated_at by design. The model only tracks
    created_at and the single status transition (pending → sent | failed).
    """

    _id: str
    _type: str
    _subject: str
    _body: str
    _status: NotificationStatus
    _created_at: datetime
    _sent_at: datetime | None
    # user_id is nullable (SET NULL on user deletion; history is kept for audit).
    _user_id: str | None = None
    _read_at: datetime | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def type(self) -> str:
        return self._type

    @property
    def subject(self) -> str:
        return self._subject

    @property
    def body(self) -> str:
        return self._body

    @property
    def status(self) -> NotificationStatus:
        return self._status

    @property
    def sent_at(self) -> datetime | None:
        return self._sent_at

    @property
    def read_at(self) -> datetime | None:
        return self._read_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    # derived property
    @property
    def is_read(self) -> bool:
        return self._read_at is not None

    # methods
    def mark_sent(self) -> None:
        """Record a successful dispatch — stamps sent_at with current UTC time in Email notification."""
        self._status = NotificationStatus.SENT
        self._sent_at = datetime.now(UTC)

    def mark_failed(self) -> None:
        """Record a failed dispatch attempt in Email notification."""
        self._status = NotificationStatus.FAILED

    def mark_read(self) -> None:
        """Mark the notification as read in In-app notification"""
        self._read_at = datetime.now(UTC)
