from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import (
    BookAuthorItemResult,
    BookCategoryResult,
    BookPublisherResult,
    ViewBookDetailCommand,
    ViewBookDetailResult,
)
from app.application.use_cases.book.view_book_detail import ViewBookDetailUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.author_entity import AuthorEntity
from app.domain.entities.book_author_entity import BookAuthorEntity
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.publisher_entity import PublisherEntity
from app.domain.exceptions.book import BookNotFoundError
from app.domain.repositories.book_repository import (
    BookFilters,
    BookStatusFilter,
    IBookRepository,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _make_publisher(pub_id: str = "pub-1", name: str = "DAW Books") -> PublisherEntity:
    now = _now()
    return PublisherEntity(
        _id=pub_id,
        _name=name,
        _website=None,
        _created_at=now,
        _updated_at=now,
    )


def _make_category(cat_id: str = "cat-1", name: str = "Fantasy") -> CategoryEntity:
    now = _now()
    return CategoryEntity(
        _id=cat_id,
        _collection_id="col-1",
        _name=name,
        _url_slug="fantasy",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_author(
    author_id: str = "auth-1", name: str = "Patrick Rothfuss"
) -> AuthorEntity:
    now = _now()
    return AuthorEntity(
        _id=author_id,
        _name=name,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_book_author(
    book_id: str = "book-1",
    author_id: str = "auth-1",
    display_order: int = 1,
    author: AuthorEntity | None = None,
) -> BookAuthorEntity:
    now = _now()
    return BookAuthorEntity(
        _book_id=book_id,
        _author_id=author_id,
        _display_order=display_order,
        _created_at=now,
        _updated_at=now,
        _author=author,
    )


def _make_book(
    book_id: str = "book-1",
    title: str = "The Name of the Wind",
    deactivated_at: datetime | None = None,
    publisher: PublisherEntity | None = None,
    category: CategoryEntity | None = None,
    authors: list[BookAuthorEntity] | None = None,
) -> BookEntity:
    now = _now()
    return BookEntity(
        _id=book_id,
        _title=title,
        _price=Decimal("19.99"),
        _stock_quantity=50,
        _language="English",
        _publisher_id=publisher.id if publisher else None,
        _category_id=category.id if category else None,
        _isbn="9780756404741",
        _description="A detailed fantasy novel...",
        _cover_url=None,
        _page_count=662,
        _published_date=date(2007, 3, 27),
        _deactivated_at=deactivated_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _publisher=publisher,
        _category=category,
        _authors=authors or [],
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._book = book
        self.last_book_id: str | None = None
        self.last_filters: BookStatusFilter | None = None

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        self.last_book_id = book_id
        self.last_filters = filters

        if self._book is None:
            return None
        if filters.status == "deactivate":
            return self._book if self._book._deactivated_at is not None else None
        if filters.status == "activate":
            return self._book if self._book._deactivated_at is None else None

        return self._book

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        return None

    async def save(self, book: BookEntity) -> None:
        pass

    async def get_inventory_metrics(self, low_stock_threshold: int) -> Any:
        pass

    async def find_low_stock(
        self, query: QueryParams, threshold: int
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    async def find_out_of_stock(
        self, query: QueryParams
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)


@pytest.mark.unit
class TestViewBookDetailUseCase:
    async def test_returns_book_detail_result_for_activated_book(self) -> None:
        publisher = _make_publisher()
        category = _make_category()
        author = _make_author()
        book_author = _make_book_author(author=author)
        book = _make_book(publisher=publisher, category=category, authors=[book_author])
        repo = FakeBookRepository(book=book)
        use_case = ViewBookDetailUseCase(db_session=AsyncMock(), book_repo=repo)

        result = await use_case.execute(
            ViewBookDetailCommand(book_id="book-1", filters=BookStatusFilter())
        )

        assert isinstance(result, ViewBookDetailResult)
        assert result.id == "book-1"
        assert result.title == "The Name of the Wind"
        assert result.is_active is True
        assert isinstance(result.publisher, BookPublisherResult)
        assert result.publisher.id == "pub-1"
        assert result.publisher.name == "DAW Books"
        assert isinstance(result.category, BookCategoryResult)
        assert result.category.id == "cat-1"
        assert result.category.name == "Fantasy"
        assert len(result.authors) == 1
        assert isinstance(result.authors[0], BookAuthorItemResult)
        assert result.authors[0].id == "auth-1"
        assert result.authors[0].name == "Patrick Rothfuss"
        assert result.authors[0].display_order == 1

    async def test_raises_book_not_found_when_repo_returns_none(self) -> None:
        repo = FakeBookRepository(book=None)
        use_case = ViewBookDetailUseCase(db_session=AsyncMock(), book_repo=repo)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(
                ViewBookDetailCommand(book_id="missing-id", filters=BookStatusFilter())
            )

    async def test_returns_deactivated_book_when_status_is_deactivate(self) -> None:
        book = _make_book(deactivated_at=_now())
        repo = FakeBookRepository(book=book)
        use_case = ViewBookDetailUseCase(db_session=AsyncMock(), book_repo=repo)

        result = await use_case.execute(
            ViewBookDetailCommand(
                book_id="book-1",
                filters=BookStatusFilter(status="deactivate"),
            )
        )

        assert isinstance(result, ViewBookDetailResult)
        assert result.is_active is False
        assert repo.last_filters == BookStatusFilter(status="deactivate")

    async def test_raises_book_not_found_for_deactivated_book_with_activate_filter(
        self,
    ) -> None:
        book = _make_book(deactivated_at=_now())
        repo = FakeBookRepository(book=book)
        use_case = ViewBookDetailUseCase(db_session=AsyncMock(), book_repo=repo)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(
                ViewBookDetailCommand(
                    book_id="book-1",
                    filters=BookStatusFilter(status="activate"),
                )
            )
