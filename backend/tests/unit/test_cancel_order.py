from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.order_dto import CancelOrderCommand, CancelOrderResult
from app.application.use_cases.order.cancel_order import CancelOrderUseCase
from app.core.constants import OrderStatus, UserRole, UserStatus
from app.domain.entities import (
    BookEntity,
    NotificationEntity,
    OrderEntity,
    OrderItemEntity,
    UserEntity,
)
from app.domain.exceptions import (
    OrderAccessDeniedError,
    OrderNotCancellableError,
    OrderNotFoundError,
)
from app.domain.repositories import (
    IBookRepository,
    INotificationRepository,
    IOrderRepository,
    IUserRepository,
)
from app.domain.repositories.book_repository import BookStatusFilter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)


def _make_item(
    book_id: str | None = "book-001", book: BookEntity | None = None
) -> OrderItemEntity:
    return OrderItemEntity(
        _id="item-001",
        _order_id="order-001",
        _book_id=book_id,
        _book_title="Clean Architecture",
        _unit_price=Decimal("19.99"),
        _quantity=2,
        _line_total=Decimal("39.98"),
        _created_at=NOW,
        _updated_at=NOW,
        _book=book,
    )


def _make_order(
    user_id: str | None = "user-001",
    status: OrderStatus = OrderStatus.PENDING,
    book_id: str | None = "book-001",
    book: BookEntity | None = None,
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
        _order_items=[_make_item(book_id=book_id, book=book)],
    )


def _make_book() -> BookEntity:
    return BookEntity(
        _id="book-001",
        _title="Clean Architecture",
        _price=Decimal("19.99"),
        _stock_quantity=10,
        _language="en",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=NOW,
        _updated_at=NOW,
        _deleted_at=None,
    )


def _make_user(user_id: str = "user-001") -> UserEntity:
    return UserEntity(
        _id=user_id,
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


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._book = book
        self.saved: list[BookEntity] = []

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return self._book if (self._book and self._book.id == book_id) else None

    async def save(self, book: BookEntity) -> None:
        self.saved.append(book)

    async def find_by_isbn(self, isbn: str) -> Any:
        return None

    async def find_all(self, *args: Any, **kwargs: Any) -> Any:
        return []

    async def count(self, *args: Any, **kwargs: Any) -> int:
        return 0

    async def exists_by_isbn(self, isbn: str) -> bool:
        return False


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

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


class FakeNotificationRepository(INotificationRepository):
    def __init__(self) -> None:
        self.saved: list[NotificationEntity] = []

    async def save(self, notification: NotificationEntity) -> None:
        self.saved.append(notification)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_use_case(
    order: OrderEntity | None = None,
    book: BookEntity | None = None,
    user: UserEntity | None = None,
) -> tuple[
    CancelOrderUseCase,
    FakeOrderRepository,
    FakeBookRepository,
    FakeNotificationRepository,
]:
    order_repo = FakeOrderRepository(order=order)
    book_repo = FakeBookRepository(book=book)
    user_repo = FakeUserRepository(user=user)
    notification_repo = FakeNotificationRepository()
    use_case = CancelOrderUseCase(
        db_session=AsyncMock(),
        order_repo=order_repo,
        notification_repo=notification_repo,
        book_repo=book_repo,
        user_repo=user_repo,
        email_notification_svc=MagicMock(),
    )
    return use_case, order_repo, book_repo, notification_repo


def _customer_cmd(
    order_id: str = "order-001",
    user_id: str = "user-001",
) -> CancelOrderCommand:
    return CancelOrderCommand(
        order_id=order_id,
        user_id=user_id,
        user_role=UserRole.USER,
    )


def _admin_cmd(
    order_id: str = "order-001",
    user_id: str = "admin-001",
) -> CancelOrderCommand:
    return CancelOrderCommand(
        order_id=order_id,
        user_id=user_id,
        user_role=UserRole.ADMIN,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCancelOrderUseCase:
    async def test_customer_cancels_pending_order_returns_cancelled_result(
        self,
    ) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.PENDING)
        use_case, *_ = _make_use_case(order=order, user=_make_user())

        result = await use_case.execute(_customer_cmd(user_id="user-001"))

        assert isinstance(result, CancelOrderResult)
        assert result.id == "order-001"
        assert result.status == OrderStatus.CANCELLED

    async def test_admin_cancels_paid_order_belonging_to_other_user(self) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.PAID)
        use_case, *_ = _make_use_case(order=order, user=_make_user())

        result = await use_case.execute(_admin_cmd(user_id="admin-001"))

        assert isinstance(result, CancelOrderResult)
        assert result.status == OrderStatus.CANCELLED

    async def test_raises_order_not_found_when_order_missing(self) -> None:
        use_case, *_ = _make_use_case(order=None)

        with pytest.raises(OrderNotFoundError):
            await use_case.execute(_customer_cmd())

    async def test_raises_access_denied_when_customer_owns_different_order(
        self,
    ) -> None:
        order = _make_order(user_id="other-user", status=OrderStatus.PENDING)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderAccessDeniedError):
            await use_case.execute(_customer_cmd(user_id="user-001"))

    async def test_raises_not_cancellable_when_customer_cancels_paid_order(
        self,
    ) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.PAID)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderNotCancellableError):
            await use_case.execute(_customer_cmd(user_id="user-001"))

    async def test_raises_not_cancellable_when_customer_cancels_shipped_order(
        self,
    ) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.SHIPPED)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderNotCancellableError):
            await use_case.execute(_customer_cmd(user_id="user-001"))

    async def test_raises_not_cancellable_when_admin_cancels_shipped_order(
        self,
    ) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.SHIPPED)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderNotCancellableError):
            await use_case.execute(_admin_cmd())

    async def test_raises_not_cancellable_when_admin_cancels_already_cancelled_order(
        self,
    ) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.CANCELLED)
        use_case, *_ = _make_use_case(order=order)

        with pytest.raises(OrderNotCancellableError):
            await use_case.execute(_admin_cmd())

    async def test_stock_restored_for_all_items(self) -> None:
        book = _make_book()
        order = _make_order(user_id="user-001", status=OrderStatus.PENDING, book=book)
        use_case, _, book_repo, _ = _make_use_case(
            order=order, book=book, user=_make_user()
        )

        await use_case.execute(_customer_cmd(user_id="user-001"))

        assert len(book_repo.saved) == 1
        assert book_repo.saved[0].stock_quantity == 12  # 10 + 2

    async def test_item_with_no_book_id_skipped_silently(self) -> None:
        order = _make_order(
            user_id="user-001", status=OrderStatus.PENDING, book_id=None
        )
        use_case, *_ = _make_use_case(order=order, user=_make_user())

        result = await use_case.execute(_customer_cmd(user_id="user-001"))

        assert result.status == OrderStatus.CANCELLED

    async def test_notification_saved_when_user_exists(self) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.PENDING)
        use_case, _, _, notification_repo = _make_use_case(
            order=order, user=_make_user("user-001")
        )

        await use_case.execute(_customer_cmd(user_id="user-001"))

        assert len(notification_repo.saved) == 1

    async def test_no_notification_when_user_not_found(self) -> None:
        order = _make_order(user_id="user-001", status=OrderStatus.PENDING)
        # user_repo returns None — simulates user soft-deleted after placing order
        use_case, _, _, notification_repo = _make_use_case(order=order, user=None)

        await use_case.execute(_customer_cmd(user_id="user-001"))

        assert len(notification_repo.saved) == 0
