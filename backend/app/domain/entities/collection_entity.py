from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .category_entity import CategoryEntity


@dataclass
class CollectionEntity:
    _id: str
    _name: str
    _url_slug: str
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None
    # Eagerly loaded (lazy="selectin" on the ORM side).
    _categories: list[CategoryEntity] = field(default_factory=list)

    # getters
    @property
    def id(self) -> str:
        return self._id

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

    @property
    def categories(self) -> list[CategoryEntity]:
        return self._categories

    # derived properties
    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    # methods
    def update(self, name: str, url_slug: str) -> None:
        """Rename the collection and/or change its URL slug."""
        self._name = name
        self._url_slug = url_slug
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """Soft-delete the collection (cascades to its categories in the DB)."""
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)
