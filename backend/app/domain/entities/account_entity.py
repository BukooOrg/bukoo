from dataclasses import dataclass
from datetime import UTC, datetime


@dataclass
class AccountEntity:
    """
    Represents one OAuth integration row.
    provider + open_id uniquely identifies an external OAuth identity.
    """

    _id: str
    _user_id: str
    _provider: str
    _open_id: str
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
    def provider(self) -> str:
        return self._provider

    @property
    def open_id(self) -> str:
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

    # setters
    @encrypted_token.setter
    def encrypted_token(self, value: str | None) -> None:
        self._encrypted_token = value

    @updated_at.setter
    def updated_at(self, value: datetime) -> None:
        self._updated_at = value

    # methods
    def update_token(self, encrypted_token: str) -> None:
        self.encrypted_token = encrypted_token
        self.updated_at = datetime.now(UTC)
