from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.constants import UserRole, UserStatus


@dataclass(frozen=True)
class UpdateAvatarCommand:
    user_id: str
    file_data: bytes
    content_type: str


@dataclass(frozen=True)
class UpdateAvatarResult:
    id: str
    email: str
    full_name: str
    date_of_birth: date | None
    role: UserRole
    status: UserStatus
    avatar_url: str | None
    have_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class SoftDeleteMeCommand:
    user_id: str
    token_payload: dict[str, object]


@dataclass(frozen=True)
class SoftDeleteMeResult:
    message: str


@dataclass(frozen=True)
class UpdateProfileCommand:
    user_id: str
    full_name: str
    date_of_birth: date | None


@dataclass(frozen=True)
class UpdateProfileResult:
    id: str
    email: str
    full_name: str
    date_of_birth: date | None
    role: UserRole
    status: UserStatus
    avatar_url: str | None
    have_password: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
