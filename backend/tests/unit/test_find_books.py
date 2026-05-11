from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import (
    BaseBookResult,
    BookAuthorItemResult,
    BookCategoryResult,
    BookPublisherResult,
    FindBooksCommand,
)
from app.application.use_cases.book.find_books import FindBooksUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.author_entity import AuthorEntity
from app.domain.entities.book_author_entity import BookAuthorEntity
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.publisher_entity import PublisherEntity
from app.domain.repositories.book_repository import BookFilters, IBookRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _make_publisher(pub_id: str = "pub-1", name: str = "Penguin") -> PublisherEntity:
    now = _now()
    return PublisherEntity(
        _id=pub_id,
        _name=name,
        _website=None,
        _created_at=now,
        _updated_at=now,
    )


def _make_category(cat_id: str = "cat-1", name: str = "Fiction") -> CategoryEntity:
    now = _now()
    return CategoryEntity(
        _id=cat_id,
        _collection_id="col-1",
        _name=name,
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_author(author_id: str = "auth-1", name: str = "Matt Haig") -> AuthorEntity:
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
    title: str = "The Midnight Library",
    price: str = "14.99",
    stock_quantity: int = 10,
    publisher: PublisherEntity | None = None,
    category: CategoryEntity | None = None,
    authors: list[BookAuthorEntity] | None = None,
) -> BookEntity:
    now = _now()
    return BookEntity(
        _id=book_id,
        _title=title,
        _price=Decimal(price),
        _stock_quantity=stock_quantity,
        _language="English",
        _publisher_id=publisher.id if publisher else None,
        _category_id=category.id if category else None,
        _isbn="9780525559474",
        _description="Between life and death...",
        _cover_url=None,
        _page_count=304,
        _published_date=date(2020, 9, 29),
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _publisher=publisher,
        _category=category,
        _authors=authors or [],
    )


def _make_paginated(
    books: list[BookEntity],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResult[BookEntity]:
    return PaginatedResult(
        items=books,
        total_items=len(books),
        page=page,
        page_size=page_size,
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, result: PaginatedResult[BookEntity] | None = None) -> None:
        self._result: PaginatedResult[BookEntity] = result or PaginatedResult(
            items=[], total_items=0, page=1, page_size=20
        )
        self.last_query: QueryParams | None = None
        self.last_filters: BookFilters | None = None

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        self.last_query = query
        self.last_filters = filters
        return self._result

    async def find_by_id(self, book_id: str) -> BookEntity | None:
        return None

    async def save(self, book: BookEntity) -> None:
        pass


@pytest.mark.unit
class TestFindBooksUseCase:
    async def test_returns_empty_paginated_result_when_no_books(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        assert isinstance(result, PaginatedResult)
        assert result.items == []
        assert result.total_items == 0

    async def test_returns_paginated_books(self) -> None:
        db_session = AsyncMock()
        books = [_make_book(book_id="b-1"), _make_book(book_id="b-2")]
        repo = FakeBookRepository(result=_make_paginated(books, page=1, page_size=20))
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        assert len(result.items) == 2
        assert all(isinstance(item, BaseBookResult) for item in result.items)
        assert result.total_items == 2
        assert result.page == 1
        assert result.page_size == 20

    async def test_applies_search_filter_via_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)
        filters = BookFilters(search="harry")

        await use_case.execute(FindBooksCommand(query=QueryParams(), filters=filters))

        assert repo.last_filters is not None
        assert repo.last_filters.search == "harry"

    async def test_applies_category_filter_via_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)
        filters = BookFilters(category_id="cat-123")

        await use_case.execute(FindBooksCommand(query=QueryParams(), filters=filters))

        assert repo.last_filters is not None
        assert repo.last_filters.category_id == "cat-123"

    async def test_applies_in_stock_filter_via_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)
        filters = BookFilters(in_stock=True)

        await use_case.execute(FindBooksCommand(query=QueryParams(), filters=filters))

        assert repo.last_filters is not None
        assert repo.last_filters.in_stock is True

    async def test_maps_entity_fields_to_base_book_result(self) -> None:
        db_session = AsyncMock()
        now = _now()
        book = BookEntity(
            _id="book-id-1",
            _title="The Midnight Library",
            _price=Decimal("14.99"),
            _stock_quantity=42,
            _language="English",
            _publisher_id=None,
            _category_id=None,
            _isbn="9780525559474",
            _description="Between life and death...",
            _cover_url="https://example.com/cover.jpg",
            _page_count=304,
            _published_date=date(2020, 9, 29),
            _deactivated_at=None,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )
        repo = FakeBookRepository(result=_make_paginated([book]))
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        item = result.items[0]
        assert item.id == "book-id-1"
        assert item.title == "The Midnight Library"
        assert item.price == Decimal("14.99")
        assert item.stock_quantity == 42
        assert item.language == "English"
        assert item.isbn == "9780525559474"
        assert item.description == "Between life and death..."
        assert item.cover_url == "https://example.com/cover.jpg"
        assert item.page_count == 304
        assert item.published_date == date(2020, 9, 29)
        assert item.is_active is True
        assert item.created_at == now
        assert item.publisher is None
        assert item.category is None
        assert item.authors == []

    async def test_maps_publisher_to_result(self) -> None:
        db_session = AsyncMock()
        publisher = _make_publisher(pub_id="pub-1", name="Penguin")
        book = _make_book(publisher=publisher)
        repo = FakeBookRepository(result=_make_paginated([book]))
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        item = result.items[0]
        assert isinstance(item.publisher, BookPublisherResult)
        assert item.publisher.id == "pub-1"
        assert item.publisher.name == "Penguin"

    async def test_maps_category_to_result(self) -> None:
        db_session = AsyncMock()
        category = _make_category(cat_id="cat-1", name="Fiction")
        book = _make_book(category=category)
        repo = FakeBookRepository(result=_make_paginated([book]))
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        item = result.items[0]
        assert isinstance(item.category, BookCategoryResult)
        assert item.category.id == "cat-1"
        assert item.category.name == "Fiction"

    async def test_maps_authors_to_result(self) -> None:
        db_session = AsyncMock()
        author = _make_author(author_id="auth-1", name="Matt Haig")
        book_author = _make_book_author(
            book_id="book-1", author_id="auth-1", display_order=1, author=author
        )
        book = _make_book(book_id="book-1", authors=[book_author])
        repo = FakeBookRepository(result=_make_paginated([book]))
        use_case = FindBooksUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute(
            FindBooksCommand(query=QueryParams(), filters=BookFilters())
        )

        item = result.items[0]
        assert len(item.authors) == 1
        author_result = item.authors[0]
        assert isinstance(author_result, BookAuthorItemResult)
        assert author_result.id == "auth-1"
        assert author_result.name == "Matt Haig"
        assert author_result.display_order == 1
