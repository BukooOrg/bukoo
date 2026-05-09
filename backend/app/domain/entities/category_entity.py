from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class CategoryEntity:
    _id: str
    _collection_id: str
    _name: str
    _url_slug: str
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def collection_id(self) -> str:
        return self._collection_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def url_slug(self) -> str:
        return self._url_slug

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    # derived properties
    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    # methods
    def update(self, collection_id: str, name: str, url_slug: str) -> None:
        """Rename the category and/or change its URL slug. Optionally, reassign collection"""
        self._collection_id = collection_id
        self._name = name
        self._url_slug = url_slug
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """Soft-delete the category."""
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
