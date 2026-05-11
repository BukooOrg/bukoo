from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal

from app.core.query_params import QueryParams
from app.domain.repositories.book_repository import BookFilters


# commands
@dataclass(frozen=True)
class FindBooksCommand:
    query: QueryParams
    filters: BookFilters = field(default_factory=BookFilters)


# results
@dataclass(frozen=True)
class BookPublisherResult:
    id: str
    name: str


@dataclass(frozen=True)
class BookCategoryResult:
    id: str
    name: str


@dataclass(frozen=True)
class BookAuthorItemResult:
    id: str
    name: str
    display_order: int


@dataclass(frozen=True)
class BaseBookResult:
    id: str
    title: str
    price: Decimal
    language: str
    stock_quantity: int
    cover_url: str | None
    isbn: str | None
    description: str | None
    page_count: int | None
    published_date: date | None
    is_active: bool
    publisher: BookPublisherResult | None
    category: BookCategoryResult | None
    authors: list[BookAuthorItemResult]
    created_at: datetime
    updated_at: datetime
