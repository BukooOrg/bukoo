from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import (
    UpdateBookStockQuantityCommand,
    UpdateBookStockQuantityResult,
)
from app.application.use_cases.book.update_book_stock_quantity import (
    UpdateBookStockQuantityUseCase,
)
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity
from app.domain.exceptions.book import BookNotFoundError
from app.domain.repositories.book_repository import (
    BookFilters,
    BookStatusFilter,
    IBookRepository,
)


def _make_book(
    book_id: str = "book-1",
    stock_quantity: int = 50,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="The Great Gatsby",
        _price=Decimal("12.99"),
        _stock_quantity=stock_quantity,
        _language="en",
        _publisher_id=None,
        _category_id=None,
        _isbn="1234567890123",
        _description=None,
        _cover_url=None,
        _page_count=180,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _publisher=None,
        _category=None,
        _authors=[],
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._books: dict[str, BookEntity] = {}
        self.saved: BookEntity | None = None
        if book is not None:
            self._books[book.id] = book

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return self._books.get(book_id)

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        return None

    async def save(self, book: BookEntity) -> None:
        self._books[book.id] = book
        self.saved = book

    async def get_inventory_metrics(self, low_stock_threshold: int) -> Any:
        pass


def _build_use_case(
    book_repo: FakeBookRepository | None = None,
) -> tuple[UpdateBookStockQuantityUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = UpdateBookStockQuantityUseCase(
        db_session=db_session,
        book_repo=book_repo or FakeBookRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestUpdateBookStockQuantityUseCase:
    async def test_updates_stock_to_new_value(self) -> None:
        book = _make_book("book-1", stock_quantity=10)
        book_repo = FakeBookRepository(book)
        use_case, db_session = _build_use_case(book_repo)
        cmd = UpdateBookStockQuantityCommand(book_id="book-1", stock_quantity=150)

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateBookStockQuantityResult)
        assert result.stock_quantity == 150
        assert result.id == "book-1"
        db_session.commit.assert_called_once()

    async def test_sets_stock_to_zero(self) -> None:
        book = _make_book("book-1", stock_quantity=25)
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo)
        cmd = UpdateBookStockQuantityCommand(book_id="book-1", stock_quantity=0)

        result = await use_case.execute(cmd)

        assert result.stock_quantity == 0

    async def test_raises_book_not_found_when_missing(self) -> None:
        book_repo = FakeBookRepository()
        use_case, _ = _build_use_case(book_repo)
        cmd = UpdateBookStockQuantityCommand(book_id="nonexistent", stock_quantity=10)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_same_quantity_is_idempotent(self) -> None:
        book = _make_book("book-1", stock_quantity=50)
        book_repo = FakeBookRepository(book)
        use_case, db_session = _build_use_case(book_repo)
        cmd = UpdateBookStockQuantityCommand(book_id="book-1", stock_quantity=50)

        result = await use_case.execute(cmd)

        assert result.stock_quantity == 50
        db_session.commit.assert_called_once()

    async def test_soft_deleted_book_treated_as_not_found(self) -> None:
        # Fake repo returns None, simulating the repo filtering out soft-deleted records.
        book_repo = FakeBookRepository()
        use_case, _ = _build_use_case(book_repo)
        cmd = UpdateBookStockQuantityCommand(book_id="deleted-book", stock_quantity=10)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)
