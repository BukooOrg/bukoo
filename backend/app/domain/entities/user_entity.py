from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import TYPE_CHECKING

from app.core.constants import UserRole, UserStatus

if TYPE_CHECKING:
    from .account_entity import AccountEntity
    from .address_entity import AddressEntity


@dataclass
class UserEntity:
    _id: str
    _email: str
    _full_name: str
    _date_of_birth: date
    _role: UserRole
    _status: UserStatus
    _hashed_password: str | None
    _avatar_url: str | None
    _last_login_at: datetime | None
    _created_at: datetime
    _updated_at: datetime
    _deleted_at: datetime | None
    # Eagerly loaded relationships (lazy="selectin" on the ORM side).
    _accounts: list[AccountEntity] = field(default_factory=list)
    _address: AddressEntity | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def email(self) -> str:
        return self._email

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def date_of_birth(self) -> date:
        return self._date_of_birth

    @property
    def role(self) -> UserRole:
        return self._role

    @property
    def status(self) -> UserStatus:
        return self._status

    @property
    def hashed_password(self) -> str | None:
        return self._hashed_password

    @property
    def avatar_url(self) -> str | None:
        return self._avatar_url

    @property
    def last_login_at(self) -> datetime | None:
        return self._last_login_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    @property
    def accounts(self) -> list[AccountEntity]:
        return self._accounts

    @property
    def address(self) -> AddressEntity | None:
        return self._address

    # derived properties
    @property
    def is_active(self) -> bool:
        return self._status == UserStatus.ACTIVE

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None

    @property
    def have_password(self) -> bool:
        return self._hashed_password is not None

    # methods
    def activate(self) -> None:
        """Transition status from pending -> active."""
        self._status = UserStatus.ACTIVE
        self._updated_at = datetime.now(UTC)

    def suspend(self) -> None:
        """Suspend an active account."""
        self._status = UserStatus.SUSPENDED
        self._updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        """Mark the user as deleted without removing the database row."""
        self._deleted_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)

    def record_login(self) -> None:
        """Stamp last_login_at with the current UTC time."""
        self._last_login_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)

    def change_role(self, role: UserRole) -> None:
        """Promote or demote the user's role."""
        self._role = role
        self._updated_at = datetime.now(UTC)

    def set_password(self, hashed_password: str) -> None:
        """Store a new bcrypt-hashed password."""
        self._hashed_password = hashed_password
        self._updated_at = datetime.now(UTC)

    def update_avatar(self, avatar_url: str | None) -> None:
        """Update the avatar URL (pass None to clear it)."""
        self._avatar_url = avatar_url
        self._updated_at = datetime.now(UTC)

    def update_profile(self, full_name: str, date_of_birth: date) -> None:
        """Update basic profile fields."""
        self._full_name = full_name
        self._date_of_birth = date_of_birth
        self._updated_at = datetime.now(UTC)
