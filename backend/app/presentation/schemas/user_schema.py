"""Pydantic v2 schemas for user profile HTTP request and response bodies."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel

from app.core.constants import UserRole, UserStatus


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
