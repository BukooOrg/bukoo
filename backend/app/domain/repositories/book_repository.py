from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity


@dataclass(frozen=True)
class BookFilters:
    search: str | None = None
    category_id: str | None = None
    author_id: str | None = None
    publisher_id: str | None = None
    collection_id: str | None = None
    language: str | None = None
    price_min: Decimal | None = None
    price_max: Decimal | None = None
    in_stock: bool | None = None
    status: Literal["activate", "deactivate", "all"] = "activate"


class IBookRepository(ABC):
    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        pass

    @abstractmethod
    async def find_by_id(self, book_id: str) -> BookEntity | None:
        pass

    @abstractmethod
    async def save(self, book: BookEntity) -> None:
        pass
