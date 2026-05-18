from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.constants import UserRole, UserStatus
from app.core.query_params import QueryParams


# commands
@dataclass(frozen=True)
class UpdateAvatarCommand:
    user_id: str
    file_data: bytes
    content_type: str


@dataclass(frozen=True)
class RemoveAvatarCommand:
    user_id: str


@dataclass(frozen=True)
class SoftDeleteMeCommand:
    user_id: str
    token_payload: dict[str, object]


@dataclass(frozen=True)
class UpdateProfileCommand:
    user_id: str
    full_name: str
    date_of_birth: date | None


@dataclass(frozen=True)
class ChangePasswordCommand:
    user_id: str
    current_password: str
    new_password: str


@dataclass(frozen=True)
class GetMyAddressCommand:
    user_id: str


@dataclass(frozen=True)
class UpsertAddressCommand:
    user_id: str
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postcode: str
    country: str


@dataclass(frozen=True)
class FindUsersCommand:
    query_params: QueryParams
    role: UserRole | None = None
    status: UserStatus | None = None


@dataclass(frozen=True)
class ViewUserProfileCommand:
    user_id: str


@dataclass(frozen=True)
class RegisterAdminCommand:
    email: str
    password: str
    full_name: str
    date_of_birth: date | None


# results
@dataclass(frozen=True)
class SoftDeleteMeResult:
    message: str


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
class RemoveAvatarResult:
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
class ChangePasswordResult:
    message: str


@dataclass(frozen=True)
class GetMyAddressResult:
    id: str
    user_id: str
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postcode: str
    country: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class UpsertAddressResult:
    id: str
    user_id: str
    recipient_name: str
    phone: str
    address_line1: str
    address_line2: str | None
    city: str
    state: str
    postcode: str
    country: str
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True)
class FindUserResult:
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
class ViewUserProfileResult:
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
class RegisterAdminResult:
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
