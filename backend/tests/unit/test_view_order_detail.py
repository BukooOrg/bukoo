from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.order_dto import (
    ViewOrderDetailCommand,
    ViewOrderDetailResult,
)
from app.application.use_cases.order.view_order_detail import ViewOrderDetailUseCase
from app.core.constants import OrderStatus, PaymentMethod, PaymentStatus, UserRole
from app.domain.entities import OrderEntity, OrderItemEntity, PaymentEntity
from app.domain.exceptions import OrderAccessDeniedError, OrderNotFoundError
from app.domain.repositories import IOrderRepository

# helpers
NOW = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)


def _make_item() -> OrderItemEntity:
    return OrderItemEntity(
        _id="item-001",
        _order_id="order-001",
        _book_id="book-001",
        _book_title="Clean Architecture",
        _unit_price=Decimal("19.99"),
        _quantity=2,
        _line_total=Decimal("39.98"),
        _created_at=NOW,
        _updated_at=NOW,
    )


def _make_payment() -> PaymentEntity:
    return PaymentEntity(
        _id="payment-001",
        _order_id="order-001",
        _method=PaymentMethod.CARD,
        _amount=Decimal("44.98"),
        _status=PaymentStatus.SUCCESS,
        _simulated_ref="SIM-ABC123",
        _created_at=NOW,
        _updated_at=NOW,
    )


def _make_order(
    user_id: str = "user-001",
    status: OrderStatus = OrderStatus.PAID,
    with_payment: bool = True,
) -> OrderEntity:
    return OrderEntity(
        _id="order-001",
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
        _order_items=[_make_item()],
        _payments=[_make_payment()] if with_payment else [],
    )


# fake repository
class FakeOrderRepository(IOrderRepository):
    def __init__(self, order: OrderEntity | None = None) -> None:
        self._order = order

    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        return self._order if (self._order and self._order.id == order_id) else None

    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        pass


# fixtures
def _make_use_case(order: OrderEntity | None = None) -> ViewOrderDetailUseCase:
    return ViewOrderDetailUseCase(
        db_session=AsyncMock(),
        order_repo=FakeOrderRepository(order=order),
    )


def _customer_cmd(
    order_id: str = "order-001",
    user_id: str = "user-001",
) -> ViewOrderDetailCommand:
    return ViewOrderDetailCommand(
        order_id=order_id,
        user_id=user_id,
        user_role=UserRole.USER,
    )


def _admin_cmd(
    order_id: str = "order-001",
    user_id: str = "admin-001",
) -> ViewOrderDetailCommand:
    return ViewOrderDetailCommand(
        order_id=order_id,
        user_id=user_id,
        user_role=UserRole.ADMIN,
    )


# tests
@pytest.mark.unit
class TestViewOrderDetailUseCase:
    async def test_customer_views_own_order_returns_result(self) -> None:
        use_case = _make_use_case(order=_make_order(user_id="user-001"))

        result = await use_case.execute(_customer_cmd(user_id="user-001"))

        assert isinstance(result, ViewOrderDetailResult)
        assert result.id == "order-001"
        assert result.status == OrderStatus.PAID
        assert len(result.items) == 1
        assert result.items[0].id == "item-001"
        assert result.payment is not None
        assert result.payment.id == "payment-001"

    async def test_admin_views_any_order_returns_result(self) -> None:
        use_case = _make_use_case(order=_make_order(user_id="user-001"))

        result = await use_case.execute(_admin_cmd(user_id="admin-001"))

        assert isinstance(result, ViewOrderDetailResult)
        assert result.id == "order-001"
        assert result.user_id == "user-001"

    async def test_raises_order_not_found_when_order_missing(self) -> None:
        use_case = _make_use_case(order=None)

        with pytest.raises(OrderNotFoundError):
            await use_case.execute(_customer_cmd())

    async def test_raises_access_denied_when_customer_views_other_user_order(
        self,
    ) -> None:
        use_case = _make_use_case(order=_make_order(user_id="other-user"))

        with pytest.raises(OrderAccessDeniedError):
            await use_case.execute(_customer_cmd(user_id="user-001"))

    async def test_payment_is_none_when_order_has_no_payments(self) -> None:
        use_case = _make_use_case(
            order=_make_order(
                user_id="user-001",
                status=OrderStatus.PENDING,
                with_payment=False,
            )
        )

        result = await use_case.execute(_customer_cmd(user_id="user-001"))

        assert result.payment is None

    async def test_admin_does_not_raise_access_denied(self) -> None:
        use_case = _make_use_case(order=_make_order(user_id="user-001"))

        result = await use_case.execute(_admin_cmd(user_id="admin-001"))

        assert result.id == "order-001"
