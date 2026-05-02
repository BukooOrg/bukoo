from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any


@dataclass
class AddressEntity:
    _id: str
    _user_id: str
    _recipient_name: str
    _phone: str
    _address_line1: str
    _address_line2: str | None
    _city: str
    _state: str
    _postcode: str
    _country: str
    _created_at: datetime
    _updated_at: datetime

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def recipient_name(self) -> str:
        return self._recipient_name

    @property
    def phone(self) -> str:
        return self._phone

    @property
    def address_line1(self) -> str:
        return self._address_line1

    @property
    def address_line2(self) -> str | None:
        return self._address_line2

    @property
    def city(self) -> str:
        return self._city

    @property
    def state(self) -> str:
        return self._state

    @property
    def postcode(self) -> str:
        return self._postcode

    @property
    def country(self) -> str:
        return self._country

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # methods
    def update(
        self,
        recipient_name: str,
        phone: str,
        address_line1: str,
        address_line2: str | None,
        city: str,
        state: str,
        postcode: str,
        country: str,
    ) -> None:
        """Replace all mutable address fields in a single operation."""
        self._recipient_name = recipient_name
        self._phone = phone
        self._address_line1 = address_line1
        self._address_line2 = address_line2
        self._city = city
        self._state = state
        self._postcode = postcode
        self._country = country
        self._updated_at = datetime.now(UTC)

    def to_snapshot(self) -> dict[str, Any]:
        """
        Return a plain dict snapshot suitable for storing in
        orders.address_snapshot (JSONB) at checkout time.
        """
        return {
            "recipient_name": self._recipient_name,
            "phone": self._phone,
            "address_line1": self._address_line1,
            "address_line2": self._address_line2,
            "city": self._city,
            "state": self._state,
            "postcode": self._postcode,
            "country": self._country,
        }
