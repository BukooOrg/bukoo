from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import (
    BookAuthorItem as CreateBookAuthorItem,
)
from app.application.dtos.book_dto import (
    CreateBookCommand,
    CreateBookResult,
)
from app.application.use_cases.book.create_book import CreateBookUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import (
    AuthorEntity,
    BookEntity,
    CategoryEntity,
    PublisherEntity,
)
from app.domain.exceptions.author import AuthorNotFoundError
from app.domain.exceptions.book import BookAlreadyExistsError
from app.domain.exceptions.category import CategoryNotFoundError
from app.domain.exceptions.publisher import PublisherNotFoundError
from app.domain.repositories.author_repository import IAuthorRepository
from app.domain.repositories.book_repository import (
    BookFilters,
    BookStatusFilter,
    IBookRepository,
)
from app.domain.repositories.category_repository import ICategoryRepository
from app.domain.repositories.publisher_repository import IPublisherRepository


def _make_publisher(pub_id: str = "pub-1") -> PublisherEntity:
    now = datetime.now(UTC)
    return PublisherEntity(
        _id=pub_id,
        _name="Test Publisher",
        _website=None,
        _created_at=now,
        _updated_at=now,
    )


def _make_category(cat_id: str = "cat-1") -> CategoryEntity:
    now = datetime.now(UTC)
    return CategoryEntity(
        _id=cat_id,
        _collection_id="col-1",
        _name="Test Category",
        _url_slug="test-category",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_author(author_id: str = "author-1") -> AuthorEntity:
    now = datetime.now(UTC)
    return AuthorEntity(
        _id=author_id,
        _name="Test Author",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, existing_isbn: str | None = None) -> None:
        self._store: dict[str, BookEntity] = {}
        self._existing_isbn = existing_isbn

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(
            items=[],
            total_items=0,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return self._store.get(book_id)

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        if self._existing_isbn and isbn == self._existing_isbn:
            return next(iter(self._store.values()), None) or _make_dummy_book()
        return None

    async def save(self, book: BookEntity, should_skip_book_authors: bool) -> None:
        self._store[book.id] = book

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


def _make_dummy_book() -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id="dummy",
        _title="Dummy",
        _price=Decimal("1.00"),
        _stock_quantity=0,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, publishers: dict[str, PublisherEntity] | None = None) -> None:
        self._publishers = publishers or {}

    async def find_all(self, query: QueryParams) -> PaginatedResult[PublisherEntity]:
        return PaginatedResult(
            items=[],
            total_items=0,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        return self._publishers.get(publisher_id)

    async def save(self, publisher: PublisherEntity) -> None:
        pass


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, categories: dict[str, CategoryEntity] | None = None) -> None:
        self._categories = categories or {}

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        return self._categories.get(category_id)

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        return None

    async def find_all(self, collection_id: str | None = None) -> list[CategoryEntity]:
        return list(self._categories.values())

    async def save(self, category: CategoryEntity) -> None:
        pass

    async def nullify_book_category(self, category_id: str) -> None:
        pass


class FakeAuthorRepository(IAuthorRepository):
    def __init__(self, authors: dict[str, AuthorEntity] | None = None) -> None:
        self._authors = authors or {}

    async def find_all(self, query: QueryParams) -> PaginatedResult[AuthorEntity]:
        return PaginatedResult(
            items=[],
            total_items=0,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def find_by_id(self, author_id: str) -> AuthorEntity | None:
        return self._authors.get(author_id)

    async def save(self, author: AuthorEntity) -> None:
        pass


def _build_use_case(
    book_repo: FakeBookRepository | None = None,
    publisher_repo: FakePublisherRepository | None = None,
    category_repo: FakeCategoryRepository | None = None,
    author_repo: FakeAuthorRepository | None = None,
) -> tuple[CreateBookUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = CreateBookUseCase(
        db_session=db_session,
        book_repo=book_repo or FakeBookRepository(),
        publisher_repo=publisher_repo or FakePublisherRepository(),
        category_repo=category_repo or FakeCategoryRepository(),
        author_repo=author_repo or FakeAuthorRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestCreateBookUseCase:
    async def test_creates_book_with_all_fields(self) -> None:
        author = _make_author("author-1")
        publisher = _make_publisher("pub-1")
        category = _make_category("cat-1")
        use_case, db_session = _build_use_case(
            publisher_repo=FakePublisherRepository({"pub-1": publisher}),
            category_repo=FakeCategoryRepository({"cat-1": category}),
            author_repo=FakeAuthorRepository({"author-1": author}),
        )
        cmd = CreateBookCommand(
            title="The Pragmatic Programmer",
            price=Decimal("49.99"),
            stock_quantity=120,
            language="English",
            isbn="9780135957059",
            description="Your journey to mastery.",
            page_count=352,
            published_date=date(2019, 9, 13),
            publisher_id="pub-1",
            category_id="cat-1",
            authors=[CreateBookAuthorItem(author_id="author-1", display_order=1)],
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateBookResult)
        assert result.title == "The Pragmatic Programmer"
        assert result.price == Decimal("49.99")
        assert result.isbn == "9780135957059"
        assert len(result.authors) == 1
        assert result.authors[0].display_order == 1
        assert result.is_active is True
        db_session.commit.assert_called_once()

    async def test_creates_book_without_optional_fields(self) -> None:
        use_case, db_session = _build_use_case()
        cmd = CreateBookCommand(
            title="Minimal Book",
            price=Decimal("9.99"),
            stock_quantity=0,
            language="English",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateBookResult)
        assert result.isbn is None
        assert result.publisher is None
        assert result.category is None
        assert result.authors == []
        assert result.is_active is True
        db_session.commit.assert_called_once()

    async def test_raises_book_already_exists_on_duplicate_isbn(self) -> None:
        book_repo = FakeBookRepository(existing_isbn="9780135957059")
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = CreateBookCommand(
            title="Duplicate ISBN",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            isbn="9780135957059",
        )

        with pytest.raises(BookAlreadyExistsError):
            await use_case.execute(cmd)

    async def test_raises_publisher_not_found(self) -> None:
        use_case, _ = _build_use_case()
        cmd = CreateBookCommand(
            title="Missing Publisher",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            publisher_id="nonexistent-pub",
        )

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_category_not_found(self) -> None:
        use_case, _ = _build_use_case()
        cmd = CreateBookCommand(
            title="Missing Category",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            category_id="nonexistent-cat",
        )

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_author_not_found(self) -> None:
        use_case, _ = _build_use_case()
        cmd = CreateBookCommand(
            title="Missing Author",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            authors=[
                CreateBookAuthorItem(author_id="nonexistent-author", display_order=1)
            ],
        )

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(cmd)

    async def test_duplicate_author_id_last_one_wins(self) -> None:
        author = _make_author("author-1")
        use_case, _ = _build_use_case(
            author_repo=FakeAuthorRepository({"author-1": author}),
        )
        cmd = CreateBookCommand(
            title="Dup Author Book",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            authors=[
                CreateBookAuthorItem(author_id="author-1", display_order=1),
                CreateBookAuthorItem(author_id="author-1", display_order=2),
            ],
        )

        result = await use_case.execute(cmd)

        assert len(result.authors) == 1
        assert result.authors[0].display_order == 2

    async def test_stock_quantity_zero_is_valid(self) -> None:
        use_case, _ = _build_use_case()
        cmd = CreateBookCommand(
            title="Zero Stock",
            price=Decimal("9.99"),
            stock_quantity=0,
            language="English",
        )

        result = await use_case.execute(cmd)

        assert result.stock_quantity == 0

    async def test_authors_non_sequential_display_order_sorted(self) -> None:
        author1 = _make_author("author-1")
        author2 = _make_author("author-2")
        use_case, _ = _build_use_case(
            author_repo=FakeAuthorRepository(
                {"author-1": author1, "author-2": author2}
            ),
        )
        cmd = CreateBookCommand(
            title="Non-Sequential Authors",
            price=Decimal("9.99"),
            stock_quantity=1,
            language="English",
            authors=[
                CreateBookAuthorItem(author_id="author-2", display_order=3),
                CreateBookAuthorItem(author_id="author-1", display_order=1),
            ],
        )

        result = await use_case.execute(cmd)

        assert len(result.authors) == 2
        assert result.authors[0].display_order == 1
        assert result.authors[1].display_order == 3
