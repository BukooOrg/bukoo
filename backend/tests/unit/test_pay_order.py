from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.payment_dto import (
    OnlineBankingDetails,
    PaymentProcessResult,
    PayOrderCommand,
    PayOrderResult,
    ProcessPaymentCommand,
)
from app.application.interfaces.payment_strategy import IPaymentStrategy
from app.application.use_cases.order.pay_order import PayOrderUseCase
from app.core.constants import (
    NotificationStatus,
    NotificationType,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.domain.entities import (
    NotificationEntity,
    OrderEntity,
    OrderItemEntity,
    PaymentEntity,
)
from app.domain.exceptions import OrderNotFoundError, OrderNotPayableError
from app.domain.repositories import (
    IBookRepository,
    INotificationRepository,
    IOrderRepository,
    IPaymentRepository,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

NOW = datetime(2026, 1, 15, 10, 30, 0, tzinfo=UTC)


def _make_order(
    status: OrderStatus = OrderStatus.PENDING,
    user_id: str = "user-001",
) -> OrderEntity:
    item = OrderItemEntity(
        _id="item-001",
        _order_id="order-001",
        _book_title="Clean Architecture",
        _unit_price=Decimal("49.90"),
        _quantity=2,
        _line_total=Decimal("99.80"),
        _created_at=NOW,
        _updated_at=NOW,
        _book_id="book-001",
    )
    return OrderEntity(
        _id="order-001",
        _user_id=user_id,
        _address_snapshot={
            "recipient_name": "John Doe",
            "phone": "0123456789",
            "street_address": "123 Jalan Utama",
            "city": "Kuala Lumpur",
            "postcode": "50480",
            "state": "Wilayah Persekutuan",
            "country": "Malaysia",
        },
        _subtotal=Decimal("99.80"),
        _shipping_cost=Decimal("5.00"),
        _total=Decimal("104.80"),
        _status=status,
        _created_at=NOW,
        _updated_at=NOW,
        _order_items=[item],
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


class FakePaymentRepository(IPaymentRepository):
    def __init__(self) -> None:
        self.saved: list[PaymentEntity] = []

    async def save(self, payment: PaymentEntity) -> None:
        self.saved.append(payment)


class FakeNotificationRepository(INotificationRepository):
    def __init__(self) -> None:
        self.saved: list[NotificationEntity] = []

    async def save(self, notification: NotificationEntity) -> None:
        self.saved.append(notification)


class FakeBookRepository(IBookRepository):
    async def find_by_id(self, *args: Any, **kwargs: Any) -> Any:
        return None

    async def find_by_isbn(self, *args: Any, **kwargs: Any) -> Any:
        return None

    async def save(self, *args: Any, **kwargs: Any) -> None:
        pass

    async def find_all(self, *args: Any, **kwargs: Any) -> Any:
        return []

    async def count(self, *args: Any, **kwargs: Any) -> int:
        return 0

    async def exists_by_isbn(self, *args: Any, **kwargs: Any) -> bool:
        return False


# ---------------------------------------------------------------------------
# Fake payment service
# ---------------------------------------------------------------------------


class FakePaymentService:
    _strategy: IPaymentStrategy

    def __init__(self, success: bool = True) -> None:
        self._success = success

    def set_strategy(self, strategy: IPaymentStrategy) -> None:
        self._payment_strategy = strategy

    async def execute_payment(
        self, command: ProcessPaymentCommand
    ) -> PaymentProcessResult:
        if self._success:
            ref = f"BANK-TXN-{command.order_id[:8].upper()}"
            return PaymentProcessResult(
                success=True, method="online_banking", simulated_ref=ref
            )
        return PaymentProcessResult(
            success=False, method="online_banking", simulated_ref=None
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_command(
    outcome: str = "success",
    order_id: str = "order-001",
    user_id: str = "user-001",
) -> PayOrderCommand:
    return PayOrderCommand(
        order_id=order_id,
        user_id=user_id,
        user_email="john@example.com",
        user_full_name="John Doe",
        payment_method=PaymentMethod.ONLINE_BANKING,
        outcome=outcome,
        online_banking_details=OnlineBankingDetails(
            bank_name="Maybank", account_number="1234567890"
        ),
    )


def _make_use_case(
    order: OrderEntity | None = None,
    payment_success: bool = True,
) -> tuple[
    PayOrderUseCase,
    FakeOrderRepository,
    FakePaymentRepository,
    FakeNotificationRepository,
]:
    db_session = AsyncMock()
    order_repo = FakeOrderRepository(order=order)
    payment_repo = FakePaymentRepository()
    notification_repo = FakeNotificationRepository()
    payment_service = FakePaymentService(success=payment_success)
    book_repo = FakeBookRepository()
    email_svc = MagicMock()

    use_case = PayOrderUseCase(
        db_session=db_session,
        order_repo=order_repo,
        payment_repo=payment_repo,
        notification_repo=notification_repo,
        payment_svc=payment_service,  # type: ignore[arg-type]
        book_repo=book_repo,  # type: ignore[arg-type]
        email_notification_svc=email_svc,
    )
    return use_case, order_repo, payment_repo, notification_repo


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestPayOrderUseCase:
    async def test_success_online_banking_returns_paid_result(self) -> None:
        order = _make_order()
        use_case, *_repos = _make_use_case(order=order)

        result = await use_case.execute(_make_command(outcome="success"))

        assert isinstance(result, PayOrderResult)
        assert result.order_status == OrderStatus.PAID
        assert result.payment.status == PaymentStatus.SUCCESS
        assert result.payment.method == PaymentMethod.ONLINE_BANKING
        assert result.payment.simulated_ref is not None
        assert result.payment.simulated_ref.startswith("BANK-TXN-")

    async def test_success_saves_order_as_paid(self) -> None:
        order = _make_order()
        use_case, order_repo, _, _ = _make_use_case(order=order)

        await use_case.execute(_make_command(outcome="success"))

        assert len(order_repo.saved) == 1
        assert order_repo.saved[0].status == OrderStatus.PAID

    async def test_success_saves_payment_record(self) -> None:
        order = _make_order()
        use_case, _, payment_repo, _ = _make_use_case(order=order)

        await use_case.execute(_make_command(outcome="success"))

        assert len(payment_repo.saved) == 1
        assert payment_repo.saved[0].status == PaymentStatus.SUCCESS

    async def test_success_creates_in_app_notification(self) -> None:
        order = _make_order()
        use_case, _, _, notification_repo = _make_use_case(order=order)

        await use_case.execute(_make_command(outcome="success"))

        assert len(notification_repo.saved) == 1
        assert notification_repo.saved[0].type == NotificationType.PAYMENT_SUCCESS
        assert notification_repo.saved[0].status == NotificationStatus.PENDING

    async def test_failure_returns_cancelled_result(self) -> None:
        order = _make_order()
        use_case, _, payment_repo, _ = _make_use_case(
            order=order, payment_success=False
        )

        result = await use_case.execute(_make_command(outcome="failure"))

        assert result.order_status == OrderStatus.CANCELLED
        assert result.payment.status == PaymentStatus.FAILED
        assert result.payment.simulated_ref is None

    async def test_failure_saves_order_as_cancelled(self) -> None:
        order = _make_order()
        use_case, order_repo, _, _ = _make_use_case(order=order, payment_success=False)

        await use_case.execute(_make_command(outcome="failure"))

        assert order_repo.saved[0].status == OrderStatus.CANCELLED

    async def test_failure_does_not_create_notification(self) -> None:
        order = _make_order()
        use_case, _, _, notification_repo = _make_use_case(
            order=order, payment_success=False
        )

        await use_case.execute(_make_command(outcome="failure"))

        assert len(notification_repo.saved) == 0

    async def test_raises_order_not_found_when_order_missing(self) -> None:
        use_case, _, _, _ = _make_use_case(order=None)

        with pytest.raises(OrderNotFoundError):
            await use_case.execute(_make_command())

    async def test_raises_order_not_found_when_different_user(self) -> None:
        order = _make_order(user_id="other-user")
        use_case, _, _, _ = _make_use_case(order=order)

        with pytest.raises(OrderNotFoundError):
            await use_case.execute(_make_command(user_id="user-001"))

    async def test_raises_order_not_payable_when_already_paid(self) -> None:
        order = _make_order(status=OrderStatus.PAID)
        use_case, _, _, _ = _make_use_case(order=order)

        with pytest.raises(OrderNotPayableError):
            await use_case.execute(_make_command())

    async def test_raises_order_not_payable_when_cancelled(self) -> None:
        order = _make_order(status=OrderStatus.CANCELLED)
        use_case, _, _, _ = _make_use_case(order=order)

        with pytest.raises(OrderNotPayableError):
            await use_case.execute(_make_command())

    async def test_commit_called_once_on_success(self) -> None:
        order = _make_order()
        db_session = AsyncMock()
        order_repo = FakeOrderRepository(order=order)
        use_case = PayOrderUseCase(
            db_session=db_session,
            order_repo=order_repo,
            payment_repo=FakePaymentRepository(),
            notification_repo=FakeNotificationRepository(),
            payment_svc=FakePaymentService(success=True),  # type: ignore[arg-type]
            book_repo=FakeBookRepository(),  # type: ignore[arg-type]
            email_notification_svc=MagicMock(),
        )

        await use_case.execute(_make_command())

        db_session.commit.assert_called_once()
