from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class PublisherEntity:
    _id: str
    _name: str
    _website: str | None
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def website(self) -> str | None:
        return self._website

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    # methods
    def update(self, name: str, website: str | None) -> None:
        self._name = name
        self._website = website
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
