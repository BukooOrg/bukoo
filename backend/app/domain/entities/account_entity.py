from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.constants import AuthProvider


@dataclass
class AccountEntity:
    _id: str
    _user_id: str
    _provider: AuthProvider
    _open_id: str | None
    _encrypted_token: str | None
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
    def provider(self) -> AuthProvider:
        return self._provider

    @property
    def open_id(self) -> str | None:
        return self._open_id

    @property
    def encrypted_token(self) -> str | None:
        return self._encrypted_token

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    # methods
    def update_token(self, encrypted_token: str) -> None:
        """Replace the stored OAuth token and stamp updated_at."""
        self._encrypted_token = encrypted_token
        self._updated_at = datetime.now(UTC)
