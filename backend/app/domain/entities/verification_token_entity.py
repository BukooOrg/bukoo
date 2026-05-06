from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.constants import VerificationTokenType


@dataclass
class VerificationTokenEntity:
    _id: str
    _user_id: str
    _token_hash: str
    _type: VerificationTokenType
    _expires_at: datetime
    _created_at: datetime
    _updated_at: datetime
    _used_at: datetime | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def token_hash(self) -> str:
        return self._token_hash

    @property
    def type(self) -> VerificationTokenType:
        return self._type

    @property
    def expires_at(self) -> datetime:
        return self._expires_at

    @property
    def used_at(self) -> datetime | None:
        return self._used_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # derived properties
    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self._expires_at

    @property
    def is_used(self) -> bool:
        return self._used_at is not None

    # methods
    def mark_used(self) -> None:
        """Consume the token so it cannot be replayed."""
        now = datetime.now(UTC)
        self._used_at = now
        self._updated_at = now
