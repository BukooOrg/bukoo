from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity


@dataclass(frozen=True)
class BookStatusFilter:
    status: Literal["activate", "deactivate", "all"] = "activate"


@dataclass(frozen=True)
class BookFilters(BookStatusFilter):
    search: str | None = None
    category_id: str | None = None
    author_id: str | None = None
    publisher_id: str | None = None
    collection_id: str | None = None
    language: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    in_stock: bool | None = None


class IBookRepository(ABC):
    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        pass

    @abstractmethod
    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        pass

    @abstractmethod
    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        pass

    @abstractmethod
    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = False
    ) -> None:
        pass
