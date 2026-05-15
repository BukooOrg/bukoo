from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import (
    BookAuthorItem,
    UpdateBookCommand,
    UpdateBookResult,
)
from app.application.use_cases.book.update_book import UpdateBookUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import (
    AuthorEntity,
    BookEntity,
    CategoryEntity,
    PublisherEntity,
)
from app.domain.entities.book_author_entity import BookAuthorEntity
from app.domain.exceptions.author import AuthorNotFoundError
from app.domain.exceptions.book import BookAlreadyExistsError, BookNotFoundError
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


def _make_book_author(
    book_id: str,
    author: AuthorEntity,
    display_order: int = 1,
) -> BookAuthorEntity:
    now = datetime.now(UTC)
    ba = BookAuthorEntity(
        _book_id=book_id,
        _author_id=author.id,
        _display_order=display_order,
        _created_at=now,
        _updated_at=now,
    )
    ba.set_author(author)
    return ba


def _make_book(
    book_id: str = "book-1",
    isbn: str | None = None,
    publisher: PublisherEntity | None = None,
    category: CategoryEntity | None = None,
    book_authors: list[BookAuthorEntity] | None = None,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="Original Title",
        _price=Decimal("29.99"),
        _stock_quantity=10,
        _language="English",
        _publisher_id=publisher.id if publisher else None,
        _category_id=category.id if category else None,
        _isbn=isbn,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _publisher=publisher,
        _category=category,
        _authors=book_authors or [],
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._books: dict[str, BookEntity] = {}
        self._isbn_index: dict[str, BookEntity] = {}
        if book is not None:
            self._books[book.id] = book
            if book.isbn is not None:
                self._isbn_index[book.isbn] = book
        self.saved: BookEntity | None = None

    def seed(self, *books: BookEntity) -> None:
        for b in books:
            self._books[b.id] = b
            if b.isbn is not None:
                self._isbn_index[b.isbn] = b

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
        return self._books.get(book_id)

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        return self._isbn_index.get(isbn)

    async def save(self, book: BookEntity, should_skip_book_authors: bool) -> None:
        self._books[book.id] = book
        self.saved = book


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, publishers: dict[str, PublisherEntity] | None = None) -> None:
        self._publishers = publishers or {}

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
) -> tuple[UpdateBookUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = UpdateBookUseCase(
        db_session=db_session,
        book_repo=book_repo or FakeBookRepository(),
        publisher_repo=publisher_repo or FakePublisherRepository(),
        category_repo=category_repo or FakeCategoryRepository(),
        author_repo=author_repo or FakeAuthorRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestUpdateBookUseCase:
    async def test_updates_scalar_fields(self) -> None:
        book = _make_book("book-1")
        book_repo = FakeBookRepository(book)
        use_case, db_session = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title="Updated Title",
            price=Decimal("59.99"),
            stock_quantity=None,
            language=None,
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateBookResult)
        assert result.title == "Updated Title"
        assert result.price == Decimal("59.99")
        assert result.stock_quantity == 10
        assert result.language == "English"
        db_session.commit.assert_called_once()

    async def test_omitting_authors_preserves_existing_authors(self) -> None:
        author = _make_author("author-1")
        ba = _make_book_author("book-1", author, display_order=1)
        book = _make_book("book-1", book_authors=[ba])
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            authors=None,
        )

        result = await use_case.execute(cmd)

        assert len(result.authors) == 1
        assert result.authors[0].display_order == 1

    async def test_empty_authors_list_clears_authors(self) -> None:
        author = _make_author("author-1")
        ba = _make_book_author("book-1", author, display_order=1)
        book = _make_book("book-1", book_authors=[ba])
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            authors=[],
        )

        result = await use_case.execute(cmd)

        assert result.authors == []

    async def test_null_publisher_id_clears_publisher(self) -> None:
        publisher = _make_publisher("pub-1")
        book = _make_book("book-1", publisher=publisher)
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            publisher_id="null",
        )

        result = await use_case.execute(cmd)

        assert result.publisher is None

    async def test_raises_book_not_found(self) -> None:
        book_repo = FakeBookRepository()
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="nonexistent",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
        )

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_book_already_exists_on_isbn_conflict(self) -> None:
        book = _make_book("book-1")
        conflicting_book = _make_book("book-2", isbn="9780135957059")
        book_repo = FakeBookRepository(book)
        book_repo.seed(conflicting_book)
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            isbn="9780135957059",
        )

        with pytest.raises(BookAlreadyExistsError):
            await use_case.execute(cmd)

    async def test_raises_author_not_found(self) -> None:
        book = _make_book("book-1")
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(
            book_repo=book_repo,
            author_repo=FakeAuthorRepository(),
        )
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            authors=[BookAuthorItem(author_id="nonexistent-author", display_order=1)],
        )

        with pytest.raises(AuthorNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_publisher_not_found(self) -> None:
        book = _make_book("book-1")
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(
            book_repo=book_repo,
            publisher_repo=FakePublisherRepository(),
        )
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            publisher_id="nonexistent-pub",
        )

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_category_not_found(self) -> None:
        book = _make_book("book-1")
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(
            book_repo=book_repo,
            category_repo=FakeCategoryRepository(),
        )
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            category_id="nonexistent-cat",
        )

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(cmd)

    async def test_replacing_authors_updates_the_list(self) -> None:
        old_author = _make_author("author-old")
        ba = _make_book_author("book-1", old_author, display_order=1)
        book = _make_book("book-1", book_authors=[ba])
        book_repo = FakeBookRepository(book)
        new_author = _make_author("author-new")
        use_case, _ = _build_use_case(
            book_repo=book_repo,
            author_repo=FakeAuthorRepository({"author-new": new_author}),
        )
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            authors=[BookAuthorItem(author_id="author-new", display_order=1)],
        )

        result = await use_case.execute(cmd)

        assert len(result.authors) == 1
        assert result.authors[0].id == "author-new"
        assert result.authors[0].display_order == 1

    async def test_same_isbn_no_conflict(self) -> None:
        # The book being updated already has isbn "9780135957059".
        # Submitting an update with the same isbn should NOT raise BookAlreadyExistsError
        # because the isbn belongs to this book itself (not a different book).
        book = _make_book("book-1", isbn="9780135957059")
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
            isbn="9780135957059",
        )

        result = await use_case.execute(cmd)

        assert result.isbn == "9780135957059"

    async def test_command_with_no_fields_leaves_book_unchanged(self) -> None:
        book = _make_book("book-1")
        original_title = book.title
        original_price = book.price
        book_repo = FakeBookRepository(book)
        use_case, db_session = _build_use_case(book_repo=book_repo)
        cmd = UpdateBookCommand(
            book_id="book-1",
            title=None,
            price=None,
            stock_quantity=None,
            language=None,
        )

        result = await use_case.execute(cmd)

        assert result.title == original_title
        assert result.price == original_price
        db_session.commit.assert_called_once()
