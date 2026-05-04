"""Pydantic v2 schemas for auth HTTP request and response bodies."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.application.validators.password import (
    COMMON_PASSWORDS,
    DIGIT_RE,
    LOWER_RE,
    SPECIAL_RE,
    UPPER_RE,
)
from app.core.constants import UserStatus


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="User password (plain text, will be hashed server-side)",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        if not UPPER_RE.search(value):
            raise ValueError("Password must contain at least one uppercase letter.")

        if not LOWER_RE.search(value):
            raise ValueError("Password must contain at least one lowercase letter.")

        if not DIGIT_RE.search(value):
            raise ValueError("Password must contain at least one digit.")

        if not SPECIAL_RE.search(value):
            raise ValueError("Password must contain at least one special character.")

        # ── Weak password checks ───────────────────────────────────────
        lowered = value.lower()

        if lowered in COMMON_PASSWORDS:
            raise ValueError("Password is too common.")

        if "password" in lowered:
            raise ValueError("Password must not contain the word 'password'.")

        # Prevent repeated characters like "aaaaaaaA1!"
        if len(set(value)) < 4:
            raise ValueError("Password is too simple or repetitive.")

        # Prevent sequences like "12345678" or "abcdefg"
        if value.isdigit() or value.isalpha():
            raise ValueError("Password must mix different character types.")

        return value


class RegisterRequest(LoginRequest):
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="User password (min 8 chars, requires uppercase, lowercase, digit, special char)",
    )
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: date = Field(..., description="ISO 8601 date (YYYY-MM-DD)")

    @field_validator("date_of_birth")
    @classmethod
    def validate_date_of_birth(cls, value: date) -> date:
        from datetime import date as date_type

        today = date_type.today()
        if value >= today:
            raise ValueError("date_of_birth must be in the past.")
        age_years = (
            today.year
            - value.year
            - ((today.month, today.day) < (value.month, value.day))
        )
        if age_years < 5:
            raise ValueError("User must be at least 5 years old.")
        return value


class RegisterResponse(BaseModel):
    id: str
    email: str
    full_name: str
    status: UserStatus
    created_at: datetime


class GoogleLoginRequest(BaseModel):
    code: str = Field(
        ...,
        description="OAuth authorization code from Google",
    )
    redirect_uri: str | None = Field(
        default=None,
        description="Redirect URI used during OAuth flow",
    )


class TokenResponse(BaseModel):
    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (typically 'bearer')",
    )


class VerifyEmailRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to verify")
    otp: str = Field(
        ..., min_length=1, description="6-digit OTP sent to the email address"
    )


class VerifyEmailResponse(BaseModel):
    email: str
    message: str


class ResendVerificationRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to resend verification to")


class ResendVerificationResponse(BaseModel):
    email: str
    message: str


class LogoutResponse(BaseModel):
    message: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address to send the reset code to")


class ForgotPasswordResponse(BaseModel):
    message: str
