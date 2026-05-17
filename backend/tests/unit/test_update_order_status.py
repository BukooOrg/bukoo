from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.order_dto import (
    UpdateOrderStatusCommand,
    UpdateOrderStatusResult,
)
from app.application.use_cases.order.update_order_status import UpdateOrderStatusUseCase
from app.core.constants import NotificationType, OrderStatus, UserRole, UserStatus
from app.domain.entities import (
    NotificationEntity,
    OrderEntity,
    OrderItemEntity,
    UserEntity,
)
from app.domain.exceptions import OrderNotFoundError, OrderStatusTransitionInvalidError
from app.domain.repositories import (
    INotificationRepository,
    IOrderRepository,
    IUserRepository,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 1, 16, 9, 0, 0, tzinfo=UTC)


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


def _make_order(status: OrderStatus = OrderStatus.PAID) -> OrderEntity:
    return OrderEntity(
        _id="order-001",
        _user_id="user-001",
        _address_snapshot={},
        _subtotal=Decimal("39.98"),
        _shipping_cost=Decimal("5.00"),
        _total=Decimal("44.98"),
        _status=status,
        _created_at=NOW,
        _updated_at=NOW,
        _order_items=[_make_item()],
    )


def _make_user() -> UserEntity:
    return UserEntity(
        _id="user-001",
        _email="user@example.com",
        _full_name="John Doe",
        _date_of_birth=date(1990, 1, 1),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password=None,
        _avatar_url=None,
        _last_login_at=None,
        _created_at=NOW,
        _updated_at=NOW,
        _deleted_at=None,
    )


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeOrderRepository(IOrderRepository):
    def __init__(self, order: OrderEntity | None = None) -> None:
        self._order = order
        self.saved: list[OrderEntity] = []

    async def find_by_id(self, order_id: str) -> OrderEntity | None:
        return self._order if (self._order and self._order.id == order_id) else None

    async def save(self, order: OrderEntity, should_skip_items: bool = True) -> None:
        self.saved.append(order)

    async def find_all(self, *args: Any, **kwargs: Any) -> Any:
        return []

    async def find_delivered_order_item(
        self, user_id: str, order_item_id: str, book_id: str
    ) -> OrderItemEntity | None:
        return None


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user

    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._user if (self._user and self._user.id == user_id) else None

    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    async def save(self, user: UserEntity) -> None:
        pass

    async def soft_delete(self, user_id: str) -> None:
        pass

    async def exists_by_email(self, email: str) -> bool:
        return False

    async def count_including_deleted(self) -> int:
        return 0


class FakeNotificationRepository(INotificationRepository):
    def __init__(self) -> None:
        self.saved: list[NotificationEntity] = []

    async def save(self, notification: NotificationEntity) -> None:
        self.saved.append(notification)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def _make_use_case(
    order: OrderEntity | None = None,
    user: UserEntity | None = None,
) -> tuple[UpdateOrderStatusUseCase, FakeOrderRepository, FakeNotificationRepository]:
    order_repo = FakeOrderRepository(order=order)
    user_repo = FakeUserRepository(user=user)
    notification_repo = FakeNotificationRepository()
    use_case = UpdateOrderStatusUseCase(
        db_session=AsyncMock(),
        order_repo=order_repo,
        user_repo=user_repo,
        notification_repo=notification_repo,
        email_notification_svc=MagicMock(),
    )
    return use_case, order_repo, notification_repo


def _cmd(
    order_id: str = "order-001",
    status: OrderStatus = OrderStatus.SHIPPED,
) -> UpdateOrderStatusCommand:
    return UpdateOrderStatusCommand(order_id=order_id, status=status)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestUpdateOrderStatusUseCase:
    # Happy path

    async def test_advance_paid_order_to_shipped_returns_shipped_result(self) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, *_ = _make_use_case(order=order, user=_make_user())

        result = await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

        assert isinstance(result, UpdateOrderStatusResult)
        assert result.id == "order-001"
        assert result.status == OrderStatus.SHIPPED

    async def test_advance_shipped_order_to_delivered_returns_delivered_result(
        self,
    ) -> None:
        order = _make_order(status=OrderStatus.SHIPPED)
        use_case, *_ = _make_use_case(order=order, user=_make_user())

        result = await use_case.execute(_cmd(status=OrderStatus.DELIVERED))

        assert isinstance(result, UpdateOrderStatusResult)
        assert result.status == OrderStatus.DELIVERED

    # Error cases

    async def test_raises_order_not_found_when_order_missing(self) -> None:
        use_case, *_ = _make_use_case(order=None)

        with pytest.raises(OrderNotFoundError):
            await use_case.execute(_cmd())

    async def test_raises_transition_invalid_when_shipping_a_pending_order(
        self,
    ) -> None:
        order = _make_order(status=OrderStatus.PENDING)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderStatusTransitionInvalidError):
            await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

    async def test_raises_transition_invalid_when_shipping_an_already_shipped_order(
        self,
    ) -> None:
        order = _make_order(status=OrderStatus.SHIPPED)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderStatusTransitionInvalidError):
            await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

    async def test_raises_transition_invalid_when_delivering_a_paid_order(
        self,
    ) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderStatusTransitionInvalidError):
            await use_case.execute(_cmd(status=OrderStatus.DELIVERED))

    async def test_raises_transition_invalid_when_transitioning_a_cancelled_order(
        self,
    ) -> None:
        order = _make_order(status=OrderStatus.CANCELLED)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderStatusTransitionInvalidError):
            await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

    # Edge cases — notifications

    async def test_shipped_notification_saved_with_correct_type(self) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, _, notification_repo = _make_use_case(order=order, user=_make_user())

        await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

        assert len(notification_repo.saved) == 1
        assert notification_repo.saved[0].type == NotificationType.ORDER_SHIPPED

    async def test_delivered_notification_saved_with_correct_type(self) -> None:
        order = _make_order(status=OrderStatus.SHIPPED)
        use_case, _, notification_repo = _make_use_case(order=order, user=_make_user())

        await use_case.execute(_cmd(status=OrderStatus.DELIVERED))

        assert len(notification_repo.saved) == 1
        assert notification_repo.saved[0].type == NotificationType.ORDER_DELIVERED

    async def test_no_notification_when_user_not_found(self) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, _, notification_repo = _make_use_case(order=order, user=None)

        await use_case.execute(_cmd(status=OrderStatus.SHIPPED))

        assert len(notification_repo.saved) == 0
