from __future__ import annotations

from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.inventory_dtos import GetInventoryMetricsResult
from app.application.use_cases.inventory.get_inventory_metrics import (
    GetInventoryMetricsUseCase,
)
from app.core.constants import LOW_STOCK_THRESHOLD
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity
from app.domain.repositories.book_repository import (
    BookFilters,
    BookInventoryMetrics,
    BookStatusFilter,
    IBookRepository,
)


class FakeBookRepository(IBookRepository):
    def __init__(self, metrics: BookInventoryMetrics | None = None) -> None:
        self._metrics = metrics or BookInventoryMetrics(
            total_sku_count=0,
            out_of_stock_count=0,
            low_stock_count=0,
            total_inventory_value=Decimal("0"),
        )
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
        self.last_threshold = low_stock_threshold
        return self._metrics


@pytest.mark.unit
class TestGetInventoryMetricsUseCase:
    async def test_returns_metrics_from_repository(self) -> None:
        db_session = AsyncMock()
        metrics = BookInventoryMetrics(
            total_sku_count=150,
            out_of_stock_count=12,
            low_stock_count=25,
            total_inventory_value=Decimal("15234.50"),
        )
        repo = FakeBookRepository(metrics=metrics)
        use_case = GetInventoryMetricsUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute()

        assert isinstance(result, GetInventoryMetricsResult)
        assert result.total_sku_count == 150
        assert result.out_of_stock_count == 12
        assert result.low_stock_count == 25
        assert result.total_inventory_value == Decimal("15234.50")

    async def test_passes_low_stock_threshold_constant_to_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = GetInventoryMetricsUseCase(db_session=db_session, book_repo=repo)

        await use_case.execute()

        assert repo.last_threshold == LOW_STOCK_THRESHOLD

    async def test_returns_zero_metrics_when_inventory_is_empty(self) -> None:
        db_session = AsyncMock()
        repo = FakeBookRepository()
        use_case = GetInventoryMetricsUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute()

        assert result.total_sku_count == 0
        assert result.out_of_stock_count == 0
        assert result.low_stock_count == 0
        assert result.total_inventory_value == Decimal("0")

    async def test_out_of_stock_not_counted_in_low_stock(self) -> None:
        db_session = AsyncMock()
        metrics = BookInventoryMetrics(
            total_sku_count=10,
            out_of_stock_count=3,
            low_stock_count=2,
            total_inventory_value=Decimal("500.00"),
        )
        repo = FakeBookRepository(metrics=metrics)
        use_case = GetInventoryMetricsUseCase(db_session=db_session, book_repo=repo)

        result = await use_case.execute()

        assert result.out_of_stock_count == 3
        assert result.low_stock_count == 2
        assert (
            result.out_of_stock_count + result.low_stock_count <= result.total_sku_count
        )
