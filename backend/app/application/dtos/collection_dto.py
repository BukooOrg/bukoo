from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.application.dtos.category_dto import BaseCategoryResult


@dataclass(frozen=True)
class CreateCollectionCommand:
    name: str
    url_slug: str


@dataclass(frozen=True)
class BaseCollectionResult:
    id: str
    name: str
    url_slug: str
    created_at: datetime
    categories: list[BaseCategoryResult]


@dataclass(frozen=True)
class FindCollectionsResult:
    collections: list[BaseCollectionResult]


@dataclass(frozen=True)
class ViewCollectionDetailCommand:
    collection_id: str


@dataclass(frozen=True)
class ViewCollectionDetailResult(BaseCollectionResult):
    pass


@dataclass(frozen=True)
class CreateCollectionResult(BaseCollectionResult):
    categories: list[BaseCategoryResult] = field(default_factory=list)
