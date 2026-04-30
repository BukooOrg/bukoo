from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

from app.core.constants import PaymentStatus


@dataclass
class PaymentEntity:
    _id: str
    _order_id: str
    _method: str
    _amount: Decimal
    _status: PaymentStatus
    _simulated_ref: str | None
    _created_at: datetime
    _updated_at: datetime

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def order_id(self) -> str:
        return self._order_id

    @property
    def method(self) -> str:
        return self._method

    @property
    def amount(self) -> Decimal:
        return self._amount

    @property
    def status(self) -> PaymentStatus:
        return self._status

    @property
    def simulated_ref(self) -> str | None:
        return self._simulated_ref

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # methods
    def mark_success(self, simulated_ref: str) -> None:
        """Record a successful payment with a simulated transaction reference."""
        self._status = PaymentStatus.SUCCESS
        self._simulated_ref = simulated_ref
        self._updated_at = datetime.now(UTC)

    def mark_failed(self) -> None:
        """Record a failed payment attempt."""
        self._status = PaymentStatus.FAILED
        self._updated_at = datetime.now(UTC)
