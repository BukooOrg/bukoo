from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


# commands
@dataclass(frozen=True)
class FindCategoriesCommand:
    collection_id: str | None = None


@dataclass(frozen=True)
class ViewCategoryDetailCommand:
    category_id: str


@dataclass(frozen=True)
class CreateCategoryCommand:
    collection_id: str
    name: str
    url_slug: str


# results
@dataclass(frozen=True)
class BaseCategoryResult:
    id: str
    collection_id: str
    name: str
    url_slug: str
    created_at: datetime


@dataclass(frozen=True)
class ViewCategoryDetailResult(BaseCategoryResult):
    pass


@dataclass(frozen=True)
class CreateCategoryResult(BaseCategoryResult):
    pass


@dataclass(frozen=True)
class FindCategoriesResult:
    categories: list[BaseCategoryResult]
