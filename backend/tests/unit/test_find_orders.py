from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.order_dto import FindOrdersCommand, OrderSummaryResult
from app.application.use_cases.order.find_orders import FindOrdersUseCase
from app.core.constants import OrderStatus
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities import OrderEntity, OrderItemEntity
from app.domain.repositories import IOrderRepository
from app.domain.repositories.order_repository import OrderFilters

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)
DEFAULT_QUERY = QueryParams(page=PageParams(page=1, page_size=20))


def _make_item(order_id: str = "order-001") -> OrderItemEntity:
    return OrderItemEntity(
        _id="item-001",
        _order_id=order_id,
        _book_id="book-001",
        _book_title="Clean Architecture",
        _unit_price=Decimal("19.99"),
        _quantity=2,
        _line_total=Decimal("39.98"),
        _created_at=NOW,
        _updated_at=NOW,
    )


def _make_order(
    order_id: str = "order-001",
    user_id: str = "user-001",
    status: OrderStatus = OrderStatus.PENDING,
) -> OrderEntity:
    return OrderEntity(
        _id=order_id,
        _user_id=user_id,
        _address_snapshot={
            "street": "123 Main St",
            "city": "Kuala Lumpur",
            "state": "WP",
            "postcode": "50000",
            "country": "Malaysia",
        },
        _subtotal=Decimal("39.98"),
        _shipping_cost=Decimal("5.00"),
        _total=Decimal("44.98"),
        _status=status,
        _created_at=NOW,
        _updated_at=NOW,
        _order_items=[_make_item(order_id=order_id)],
    )


# ---------------------------------------------------------------------------
# Fake repository
# ---------------------------------------------------------------------------


class FakeOrderRepository(IOrderRepository):
    def __init__(self, orders: list[OrderEntity] | None = None) -> None:
        self._orders: list[OrderEntity] = orders or []
        self._last_query: QueryParams | None = None
        self._last_filters: OrderFilters | None = None

    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        return next((o for o in self._orders if o.id == order_id), None)

    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        pass

    async def find_all(
        self, query: QueryParams, filters: OrderFilters
    ) -> PaginatedResult[OrderEntity]:
        self._last_query = query
        self._last_filters = filters

        filtered = list(self._orders)
        if filters.user_id is not None:
            filtered = [o for o in filtered if o.user_id == filters.user_id]
        if filters.status is not None:
            filtered = [o for o in filtered if o.status == filters.status]

        offset = query.page.offset
        limit = query.page.limit
        page_items = filtered[offset : offset + limit]

        return PaginatedResult(
            items=page_items,
            total_items=len(filtered),
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def find_delivered_order_item(
        self, user_id: str, order_item_id: str, book_id: str
    ) -> OrderItemEntity | None:
        return None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_use_case(
    orders: list[OrderEntity] | None = None,
) -> tuple[FindOrdersUseCase, FakeOrderRepository]:
    repo = FakeOrderRepository(orders=orders)
    use_case = FindOrdersUseCase(db_session=AsyncMock(), order_repo=repo)
    return use_case, repo


def _cmd(
    query: QueryParams = DEFAULT_QUERY,
    filters: OrderFilters = OrderFilters(),
) -> FindOrdersCommand:
    return FindOrdersCommand(query_params=query, filters=filters)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFindOrdersUseCase:
    async def test_returns_paginated_result_of_order_summary(self) -> None:
        orders = [_make_order(order_id=f"order-{i:03d}") for i in range(3)]
        use_case, _ = _make_use_case(orders=orders)

        result = await use_case.execute(_cmd())

        assert isinstance(result, PaginatedResult)
        assert len(result.items) == 3
        assert all(isinstance(item, OrderSummaryResult) for item in result.items)

    async def test_pagination_fields_match_query_params(self) -> None:
        orders = [_make_order(order_id=f"order-{i:03d}") for i in range(3)]
        use_case, _ = _make_use_case(orders=orders)
        query = QueryParams(page=PageParams(page=1, page_size=20))

        result = await use_case.execute(_cmd(query=query))

        assert result.total_items == 3
        assert result.page == 1
        assert result.page_size == 20

    async def test_total_pages_computed_correctly(self) -> None:
        orders = [_make_order(order_id=f"order-{i:03d}") for i in range(45)]
        use_case, _ = _make_use_case(orders=orders)
        query = QueryParams(page=PageParams(page=1, page_size=20))

        result = await use_case.execute(_cmd(query=query))

        assert result.total_pages == 3

    async def test_empty_result_returns_zero_total_and_pages(self) -> None:
        use_case, _ = _make_use_case(orders=[])

        result = await use_case.execute(_cmd())

        assert result.items == []
        assert result.total_items == 0
        assert result.total_pages == 0

    async def test_filters_passed_through_to_repo(self) -> None:
        use_case, repo = _make_use_case(orders=[])
        d_from = date(2026, 1, 1)
        d_to = date(2026, 12, 31)
        filters = OrderFilters(
            user_id="user-001",
            status=OrderStatus.PAID,
            date_from=d_from,
            date_to=d_to,
        )

        await use_case.execute(_cmd(filters=filters))

        assert repo._last_filters is not None
        assert repo._last_filters.user_id == "user-001"
        assert repo._last_filters.status == OrderStatus.PAID
        assert repo._last_filters.date_from == d_from
        assert repo._last_filters.date_to == d_to

    async def test_query_params_passed_through_to_repo(self) -> None:
        use_case, repo = _make_use_case(orders=[])
        query = QueryParams(page=PageParams(page=3, page_size=10))

        await use_case.execute(_cmd(query=query))

        assert repo._last_query is not None
        assert repo._last_query.page.page == 3
        assert repo._last_query.page.page_size == 10

    async def test_item_count_reflects_order_items_length(self) -> None:
        order = _make_order()
        use_case, _ = _make_use_case(orders=[order])

        result = await use_case.execute(_cmd())

        assert result.items[0].item_count == 1

    async def test_summary_fields_mapped_correctly(self) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, _ = _make_use_case(orders=[order])

        result = await use_case.execute(_cmd())

        item = result.items[0]
        assert item.id == "order-001"
        assert item.user_id == "user-001"
        assert item.status == OrderStatus.PAID
        assert item.total == Decimal("44.98")
        assert item.created_at == NOW
        assert item.updated_at == NOW

    async def test_has_next_and_has_prev_on_paginated_result(self) -> None:
        orders = [_make_order(order_id=f"order-{i:03d}") for i in range(25)]
        use_case, _ = _make_use_case(orders=orders)
        query = QueryParams(page=PageParams(page=2, page_size=10))

        result = await use_case.execute(_cmd(query=query))

        assert result.has_prev is True
        assert result.has_next is True
