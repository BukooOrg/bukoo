from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Self, TypeVar

from pydantic import BaseModel, Field, model_validator

from app.application.dtos.book_dto import BaseBookResult, FindBooksCommand
from app.application.validators import Isbn13Str
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.core.util import build_public_url
from app.domain.repositories.book_repository import BookFilters
from app.presentation.schemas.list_schema import ListQueryRequest


# requests
class ViewBookDetailQueryRequest(BaseModel):
    status: Literal["activate", "deactivate", "all"] = Field(
        default="activate",
        description="Filter books by their current operational status.",
        examples=["activate", "all"],
    )


class BookListQueryRequest(ListQueryRequest, ViewBookDetailQueryRequest):
    category_id: str | None = None
    author_id: str | None = None
    publisher_id: str | None = None
    collection_id: str | None = None
    language: str | None = None
    price_min: Decimal | None = Field(default=None, ge=0)
    price_max: Decimal | None = Field(default=None, ge=0)
    in_stock: bool | None = None

    @model_validator(mode="after")
    def validate_price_range(self) -> Self:
        if (
            self.price_min is not None
            and self.price_max is not None
            and self.price_max < self.price_min
        ):
            raise ValueError("price_max must be greater than or equal to price_min.")
        return self

    def to_command(self) -> FindBooksCommand:
        return FindBooksCommand(
            query_params=QueryParams(
                page=PageParams(page=self.page, page_size=self.page_size),
                sorts=parse_sort(self.sort),
                search=self.search,
            ),
            filters=BookFilters(
                search=self.search,
                category_id=self.category_id,
                author_id=self.author_id,
                publisher_id=self.publisher_id,
                collection_id=self.collection_id,
                language=self.language,
                price_min=self.price_min,
                price_max=self.price_max,
                in_stock=self.in_stock,
                status=self.status,
            ),
        )


class BookAuthorItemRequest(BaseModel):
    author_id: str
    display_order: int = Field(ge=1)


class CreateBookRequest(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    price: Decimal = Field(gt=0, decimal_places=2)
    stock_quantity: int = Field(ge=0)
    language: str = Field(min_length=1, max_length=100)
    isbn: Isbn13Str | None = Field(default=None)
    description: str | None = Field(default=None, max_length=5000)
    page_count: int | None = Field(default=None, ge=1)
    published_date: date | None = None
    publisher_id: str | None = None
    category_id: str | None = None
    authors: list[BookAuthorItemRequest] = Field(default_factory=list)


class UpdateBookRequest(BaseModel):
    title: str | None = Field(min_length=1, max_length=500, default=None)
    price: Decimal | None = Field(gt=0, decimal_places=2, default=None)
    stock_quantity: int | None = Field(ge=0, default=None)
    language: str | None = Field(min_length=1, max_length=100, default=None)
    isbn: Isbn13Str | None = Field(default=None)
    description: str | None = Field(default=None, max_length=5000)
    cover_url: None = None
    page_count: int | None = Field(default=None, ge=1)
    published_date: date | None = None
    publisher_id: str | None = None
    category_id: str | None = None
    authors: list[BookAuthorItemRequest] | None = Field(default=None)


class UpdateBookStockQuantityRequest(BaseModel):
    stock_quantity: int = Field(ge=0)


# responses
class BookPublisherResponse(BaseModel):
    id: str
    name: str


class BookCategoryResponse(BaseModel):
    id: str
    name: str


class BookAuthorItemResponse(BaseModel):
    id: str
    name: str
    display_order: int


class BaseBookResponse(BaseModel):
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
    publisher: BookPublisherResponse | None
    category: BookCategoryResponse | None
    authors: list[BookAuthorItemResponse]
    created_at: datetime
    updated_at: datetime


class ViewBookDetailResponse(BaseBookResponse):
    pass


class CreateBookResponse(BaseBookResponse):
    pass


class UpdateBookResponse(BaseBookResponse):
    pass


class SoftDeleteBookResponse(BaseBookResponse):
    pass


class DeactivateBookResponse(BaseBookResponse):
    pass


class ActivateBookResponse(BaseBookResponse):
    pass


class UpdateBookStockQuantityResponse(BaseBookResponse):
    pass


class UploadBookCoverResponse(BaseBookResponse):
    pass


T = TypeVar("T", bound=BaseBookResult)
P = TypeVar("P", bound=BaseBookResponse)


def build_base_book_response(book_result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=book_result.id,
        title=book_result.title,
        price=book_result.price,
        language=book_result.language,
        stock_quantity=book_result.stock_quantity,
        cover_url=build_public_url(book_result.cover_url),
        isbn=book_result.isbn,
        description=book_result.description,
        page_count=book_result.page_count,
        published_date=book_result.published_date,
        is_active=book_result.is_active,
        publisher=(
            BookPublisherResponse(
                id=book_result.publisher.id, name=book_result.publisher.name
            )
            if book_result.publisher
            else None
        ),
        category=(
            BookCategoryResponse(
                id=book_result.category.id, name=book_result.category.name
            )
            if book_result.category
            else None
        ),
        authors=[
            BookAuthorItemResponse(id=a.id, name=a.name, display_order=a.display_order)
            for a in book_result.authors
        ],
        created_at=book_result.created_at,
        updated_at=book_result.updated_at,
    )
