from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from app.core.constants import OrderStatus

if TYPE_CHECKING:
    from .order_item_entity import OrderItemEntity
    from .payment_entity import PaymentEntity


# todo: update field like subtotal, shipping cost, total when the order quantity is updated.
@dataclass
class OrderEntity:
    _id: str
    _address_snapshot: dict[str, Any]
    _subtotal: Decimal
    _shipping_cost: Decimal
    _total: Decimal
    _status: OrderStatus
    _created_at: datetime
    _updated_at: datetime
    # user_id is nullable (SET NULL on user deletion for audit retention).
    _user_id: str | None = None
    # Eagerly loaded (lazy="selectin" on OrderModel).
    _order_items: list[OrderItemEntity] = field(default_factory=list)
    # order by payment.updated_at desc: the first payment is the latest
    _payments: list[PaymentEntity] = field(default_factory=list)

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str | None:
        return self._user_id

    @property
    def address_snapshot(self) -> dict[str, Any]:
        return self._address_snapshot

    @property
    def subtotal(self) -> Decimal:
        return self._subtotal

    @property
    def shipping_cost(self) -> Decimal:
        return self._shipping_cost

    @property
    def total(self) -> Decimal:
        return self._total

    @property
    def status(self) -> OrderStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def order_items(self) -> list[OrderItemEntity]:
        return list(self._order_items)

    @property
    def payments(self) -> list[PaymentEntity]:
        return self._payments

    @property
    def latest_payment(self) -> PaymentEntity | None:
        return self._payments[0] if len(self._payments) > 0 else None

    # helper methods
    def _calculate_totals(self) -> None:
        """Recompute subtotal and total from current line items."""
        self._subtotal = sum((i.line_total for i in self._order_items), Decimal("0"))
        self._total = self._subtotal + self._shipping_cost

    # methods
    def mark_paid(self) -> None:
        """Transition order status to paid after a successful payment."""
        self._status = OrderStatus.PAID
        self._updated_at = datetime.now(UTC)

    def mark_shipped(self) -> None:
        """Transition order status to shipped."""
        self._status = OrderStatus.SHIPPED
        self._updated_at = datetime.now(UTC)

    def mark_delivered(self) -> None:
        """Transition order status to delivered."""
        self._status = OrderStatus.DELIVERED
        self._updated_at = datetime.now(UTC)

    def cancel(self) -> None:
        """Cancel the order (only valid while pending or paid)."""
        if self._status not in (OrderStatus.PENDING, OrderStatus.PAID):
            raise ValueError(f"Cannot cancel an order with status {self._status!r}.")
        self._status = OrderStatus.CANCELLED
        self._updated_at = datetime.now(UTC)

    def add_order_item(self, order_item: OrderItemEntity) -> None:
        """Append a line item (used during order construction)."""
        self._order_items.append(order_item)
        self._calculate_totals()
        self._updated_at = datetime.now(UTC)

    def remove_order_item(self, order_item_id: str) -> None:
        """Remove a line item by its id."""
        before = len(self._order_items)
        self._order_items = [i for i in self._order_items if i.id != order_item_id]

        if len(self._order_items) == before:
            raise ValueError(f"OrderItem {order_item_id!r} not found in this order.")

        self._calculate_totals()
        self._updated_at = datetime.now(UTC)

    def update_qty(self, order_item_id: str, qty: int) -> None:
        """Change the quantity of a specific line item."""
        item: OrderItemEntity | None = next(
            (i for i in self._order_items if i.id == order_item_id), None
        )

        if item is None:
            raise ValueError(f"OrderItem {order_item_id!r} not found in this order.")

        item.change_quantity(qty)
        self._calculate_totals()
        self._updated_at = datetime.now(UTC)
