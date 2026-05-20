from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import DeactivateBookCommand, DeactivateBookResult
from app.application.use_cases.book.deactivate_book import DeactivateBookUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity
from app.domain.exceptions.book import BookAlreadyDeactivatedError, BookNotFoundError
from app.domain.repositories.book_repository import (
    BookFilters,
    BookStatusFilter,
    IBookRepository,
)


def _make_book(
    book_id: str = "book-1",
    deactivated_at: datetime | None = None,
) -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="The Great Gatsby",
        _price=Decimal("12.99"),
        _stock_quantity=50,
        _language="en",
        _publisher_id=None,
        _category_id=None,
        _isbn="1234567890123",
        _description=None,
        _cover_url=None,
        _page_count=180,
        _published_date=None,
        _deactivated_at=deactivated_at,
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
) -> tuple[DeactivateBookUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = DeactivateBookUseCase(
        db_session=db_session,
        book_repo=book_repo or FakeBookRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestDeactivateBookUseCase:
    async def test_deactivates_active_book(self) -> None:
        book = _make_book("book-1")
        book_repo = FakeBookRepository(book)
        use_case, db_session = _build_use_case(book_repo)
        cmd = DeactivateBookCommand(book_id="book-1")

        result = await use_case.execute(cmd)

        assert isinstance(result, DeactivateBookResult)
        assert result.is_active is False
        assert result.id == "book-1"
        db_session.commit.assert_called_once()

    async def test_raises_book_not_found_when_missing(self) -> None:
        book_repo = FakeBookRepository()
        use_case, _ = _build_use_case(book_repo)
        cmd = DeactivateBookCommand(book_id="nonexistent")

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_book_already_deactivated(self) -> None:
        book = _make_book("book-1", deactivated_at=datetime.now(UTC))
        book_repo = FakeBookRepository(book)
        use_case, _ = _build_use_case(book_repo)
        cmd = DeactivateBookCommand(book_id="book-1")

        with pytest.raises(BookAlreadyDeactivatedError):
            await use_case.execute(cmd)

    async def test_soft_deleted_book_treated_as_not_found(self) -> None:
        # The fake repo returns None for soft-deleted books (repo always filters
        # deleted_at IS NULL). Verify the use case raises BookNotFoundError.
        book_repo = FakeBookRepository()  # empty — simulates repo hiding deleted record
        use_case, _ = _build_use_case(book_repo)
        cmd = DeactivateBookCommand(book_id="deleted-book")

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)
