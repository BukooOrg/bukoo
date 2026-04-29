"""Pydantic v2 schemas for auth HTTP request and response bodies."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.application.validators.password import (
    COMMON_PASSWORDS,
    DIGIT_RE,
    LOWER_RE,
    SPECIAL_RE,
    UPPER_RE,
)


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
    full_name: str


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
