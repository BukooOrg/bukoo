"""Pydantic v2 schemas for user profile HTTP request and response bodies."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field, field_validator

from app.application.validators import DateOfBirth
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
