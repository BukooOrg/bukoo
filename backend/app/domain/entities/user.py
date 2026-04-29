"""
User domain entities.
Pure Python dataclasses — no ORM, no Pydantic, no external dependencies.

UserEntity   : core identity. One per person.
AccountEntity: one OAuth integration record per (user, provider) pair.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.core.constants import UserRole, UserStatus


@dataclass
class UserEntity:
    id: str
    email: str
    full_name: str
    role: UserRole
    status: UserStatus
    hashed_password: str | None
    avatar_url: str | None
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime | None

    @property
    def is_active(self) -> bool:
        return self.status == UserStatus.ACTIVE and self.deleted_at is None

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None

    @property
    def has_password(self) -> bool:
        """False for OAuth-only accounts."""
        return self.hashed_password is not None

    def activate(self) -> None:
        """Call after successful email verification."""
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.now(UTC)

    def record_login(self) -> None:
        self.last_login_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def soft_delete(self) -> None:
        self.deleted_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)

    def change_role(self, new_role: UserRole) -> None:
        self.role = new_role
        self.updated_at = datetime.now(UTC)

    def update_avatar(self, url: str) -> None:
        self.avatar_url = url
        self.updated_at = datetime.now(UTC)

    def set_password(self, hashed: str) -> None:
        """Set or change the credential password hash."""
        self.hashed_password = hashed
        self.updated_at = datetime.now(UTC)
