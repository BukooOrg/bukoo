from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class SortOrder:
    field: str
    direction: Literal["asc", "desc"] = "asc"


@dataclass(frozen=True)
class PageParams:
    page: int = 1
    page_size: int = 20

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


@dataclass(frozen=True)
class QueryParams:
    page: PageParams = field(default_factory=PageParams)
    sorts: list[SortOrder] = field(default_factory=list)
    search: str | None = None


@dataclass(frozen=True)
class PaginatedResult[T]:
    items: list[T]
    total_items: int
    page: int
    page_size: int

    @property
    def total_pages(self) -> int:
        if self.total_items == 0:
            return 0
        return math.ceil(self.total_items / self.page_size)

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_prev(self) -> bool:
        return self.page > 1


def parse_sort(sort_str: str | None) -> list[SortOrder]:
    """Parse a sort string into SortOrder objects.

    Examples:
        "-created_at"      → [SortOrder("created_at", "desc")]
        "name,-updated_at" → [SortOrder("name", "asc"), SortOrder("updated_at", "desc")]
    """
    if not sort_str:
        return []
    result: list[SortOrder] = []
    for token in sort_str.split(","):
        token = token.strip()
        direction: Literal["asc", "desc"]
        if token.startswith("-"):
            field_name = token[1:].strip()
            direction = "desc"
        else:
            field_name = token
            direction = "asc"
        if field_name:
            result.append(SortOrder(field=field_name, direction=direction))
    return result
