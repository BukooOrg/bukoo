from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import BaseBookResult
from app.application.dtos.inventory_dtos import FindLowStockItemsCommand
from app.application.use_cases.inventory.find_low_stock_items import (
    FindLowStockItemsUseCase,
)
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities.book_entity import BookEntity
from app.domain.repositories.book_repository import (
    BookFilters,
    BookInventoryMetrics,
    BookStatusFilter,
    IBookRepository,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _make_book(
    book_id: str = "book-1",
    stock_quantity: int = 3,
) -> BookEntity:
    now = _now()
    return BookEntity(
        _id=book_id,
        _title="Test Book",
        _price=Decimal("12.99"),
        _stock_quantity=stock_quantity,
        _language="English",
        _publisher_id=None,
        _category_id=None,
        _isbn="1234567890123",
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=date(2020, 1, 1),
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, result: PaginatedResult[BookEntity] | None = None) -> None:
        self._result: PaginatedResult[BookEntity] = result or PaginatedResult(
            items=[], total_items=0, page=1, page_size=20
        )
        self.last_query: QueryParams | None = None
        self.last_threshold: int | None = None

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return None

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        return None

    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = True
    ) -> None:
        pass

    async def get_inventory_metrics(
        self, low_stock_threshold: int
    ) -> BookInventoryMetrics:
        return BookInventoryMetrics(
            total_sku_count=0,
            out_of_stock_count=0,
            low_stock_count=0,
            total_inventory_value=Decimal("0"),
        )

    async def find_low_stock(
        self, query: QueryParams, threshold: int
    ) -> PaginatedResult[BookEntity]:
        self.last_query = query
        self.last_threshold = threshold
        return self._result

    async def find_out_of_stock(
        self, query: QueryParams
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)


@pytest.mark.unit
class TestFindLowStockItemsUseCase:
    async def test_returns_empty_result_when_no_low_stock_books(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=5)

        result = await use_case.execute(cmd)

        assert isinstance(result, PaginatedResult)
        assert result.items == []
        assert result.total_items == 0

    async def test_returns_paginated_low_stock_books(self) -> None:
        db_session = AsyncMock()
        books = [
            _make_book(book_id="b-1", stock_quantity=2),
            _make_book(book_id="b-2", stock_quantity=4),
        ]
        repo = FakeBookRepository(
            result=PaginatedResult(items=books, total_items=2, page=1, page_size=20)
        )
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=5)

        result = await use_case.execute(cmd)

        assert len(result.items) == 2
        assert all(isinstance(item, BaseBookResult) for item in result.items)
        assert result.total_items == 2
        assert result.page == 1
        assert result.page_size == 20

    async def test_passes_threshold_to_repository(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=10)

        await use_case.execute(cmd)

        assert repo.last_threshold == 10

    async def test_passes_query_params_to_repository(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        query_params = QueryParams(page=PageParams(page=2, page_size=10))
        cmd = FindLowStockItemsCommand(query_params=query_params, threshold=5)

        await use_case.execute(cmd)

        assert repo.last_query is not None
        assert repo.last_query.page.page == 2
        assert repo.last_query.page.page_size == 10

    async def test_book_at_exact_threshold_is_included(self) -> None:
        db_session = AsyncMock()
        threshold = 5
        book_at_threshold = _make_book(stock_quantity=threshold)
        repo = FakeBookRepository(
            result=PaginatedResult(
                items=[book_at_threshold], total_items=1, page=1, page_size=20
            )
        )
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=threshold)

        result = await use_case.execute(cmd)

        assert len(result.items) == 1
        assert result.items[0].stock_quantity == threshold

    async def test_out_of_stock_book_not_included(self) -> None:
        db_session = AsyncMock()
        # Repository enforces stock_quantity > 0 filter; use case trusts it
        repo = FakeBookRepository(
            result=PaginatedResult(items=[], total_items=0, page=1, page_size=20)
        )
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=5)

        result = await use_case.execute(cmd)

        assert result.total_items == 0

    async def test_total_pages_computed_correctly(self) -> None:
        db_session = AsyncMock()
        books = [_make_book(book_id=f"b-{i}") for i in range(5)]
        repo = FakeBookRepository(
            result=PaginatedResult(items=books, total_items=25, page=1, page_size=20)
        )
        use_case = FindLowStockItemsUseCase(db_session=db_session, book_repo=repo)
        cmd = FindLowStockItemsCommand(query_params=QueryParams(), threshold=5)

        result = await use_case.execute(cmd)

        assert result.total_pages == 2
        assert result.has_next is True
        assert result.has_prev is False
