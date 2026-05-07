"""Pydantic v2 schemas for user profile HTTP request and response bodies."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.application.validators import DateOfBirth, PasswordStr, PhoneNumber
from app.core.constants import UserRole, UserStatus


class SoftDeleteMeResponse(BaseModel):
    message: str


class UpdateProfileRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    date_of_birth: DateOfBirth | None = Field(
        None, description="ISO 8601 date (YYYY-MM-DD)"
    )

    @field_validator("full_name")
    @classmethod
    def strip_and_validate_full_name(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("full_name must not be empty or whitespace.")
        return stripped


class UserProfileResponse(BaseModel):
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


class ChangePasswordRequest(BaseModel):
    current_password: PasswordStr = Field(
        ...,
        description="User current password",
    )
    new_password: PasswordStr = Field(
        ...,
        description="User new password to be set (plain text, will be hashed server-side)",
    )


class ChangePasswordResponse(BaseModel):
    message: str


class UpsertAddressRequest(BaseModel):
    recipient_name: str = Field(..., min_length=2, max_length=255)
    phone: PhoneNumber = Field(...)
    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: str | None = Field(None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    postcode: str = Field(..., min_length=1, max_length=20)
    country: str = Field(..., min_length=1, max_length=100)

    @field_validator(
        "recipient_name",
        "address_line1",
        "city",
        "state",
        "postcode",
        "country",
        mode="before",
    )
    @classmethod
    def strip_and_reject_blank(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            if not stripped:
                raise ValueError("field must not be blank or whitespace-only")
            return stripped
        return v

    @field_validator("address_line2", mode="before")
    @classmethod
    def strip_address_line2(cls, v: object) -> object:
        if isinstance(v, str):
            stripped = v.strip()
            return stripped if stripped else None
        return v


class AddressResponse(BaseModel):
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
