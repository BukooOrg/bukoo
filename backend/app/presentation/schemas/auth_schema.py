"""Pydantic v2 schemas for auth HTTP request and response bodies."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.application.validators import DateOfBirth, OTPStr, PasswordStr
from app.core.constants import UserStatus


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: PasswordStr = Field(
        ...,
        description="User password (plain text, will be hashed server-side)",
    )


class RegisterRequest(LoginRequest):
    password: PasswordStr = Field(
        ...,
        description="User password (plain text, will be hashed server-side)",
    )
    full_name: str = Field(..., min_length=2, max_length=100)
    date_of_birth: DateOfBirth = Field(..., description="ISO 8601 date (YYYY-MM-DD)")


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
    otp: OTPStr = Field(..., description="6-digit OTP sent to the email address")


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


class VerifyPasswordResetResponse(BaseModel):
    valid: bool


class ResetPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address the reset code was sent to")
    otp: OTPStr = Field(..., description="6-digit OTP received in the reset email")
    new_password: PasswordStr = Field(
        ...,
        description="New password (min 8 chars, requires uppercase, lowercase, digit, special char)",
    )


class ResetPasswordResponse(BaseModel):
    message: str


class OAuthLoginUrlResponse(BaseModel):
    url: str = Field(
        ...,
        description="OAuth provider authorization URL; redirect the browser to this URL",
    )
