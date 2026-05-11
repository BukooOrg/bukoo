from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from app.core.query_params import QueryParams
from app.domain.repositories.book_repository import BookFilters, BookStatusFilter


# commands
@dataclass(frozen=True)
class FindBooksCommand:
    query: QueryParams
    filters: BookFilters = field(default_factory=BookFilters)


@dataclass(frozen=True)
class ViewBookDetailCommand:
    book_id: str
    filters: BookStatusFilter = field(default_factory=BookStatusFilter)


# create book
@dataclass(frozen=True)
class BookAuthorItem:
    author_id: str
    display_order: int


@dataclass(frozen=True)
class CreateBookCommand:
    title: str
    price: Decimal
    stock_quantity: int
    language: str
    isbn: str | None = None
    description: str | None = None
    page_count: int | None = None
    published_date: date | None = None
    publisher_id: str | None = None
    category_id: str | None = None
    authors: list[BookAuthorItem] = field(default_factory=list)


@dataclass(frozen=True)
class UpdateBookCommand:
    book_id: str
    title: str | None
    price: Decimal | None
    stock_quantity: int | None
    language: str | None
    isbn: str | None | Literal["null"] = None
    description: str | None | Literal["null"] = None
    page_count: int | None | Literal["null"] = None
    published_date: date | None | Literal["null"] = None
    publisher_id: str | None | Literal["null"] = None
    category_id: str | None | Literal["null"] = None
    authors: list[BookAuthorItem] | None | Literal["null"] = None


@dataclass(frozen=True)
class DeactivateBookCommand:
    book_id: str


@dataclass(frozen=True)
class ActivateBookCommand:
    book_id: str


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


@dataclass(frozen=True)
class ViewBookDetailResult(BaseBookResult):
    pass


@dataclass(frozen=True)
class CreateBookResult(BaseBookResult):
    pass


class UpdateBookResult(BaseBookResult):
    pass


class DeactivateBookResult(BaseBookResult):
    pass


class ActivateBookResult(BaseBookResult):
    pass
