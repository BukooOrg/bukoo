from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.constants import UserStatus


@dataclass(frozen=True)
class RegisterCommand:
    email: str
    password: str
    full_name: str
    date_of_birth: date


@dataclass(frozen=True)
class RegisterResult:
    id: str
    email: str
    full_name: str
    status: UserStatus
    created_at: datetime


@dataclass(frozen=True)
class LoginCommand:
    email: str
    password: str


@dataclass(frozen=True)
class GoogleLoginCommand:
    code: str
    redirect_uri: str


@dataclass(frozen=True)
class AuthResult:
    user_id: str
    email: str
    is_new_user: bool


@dataclass(frozen=True)
class TokenDTO:
    access_token: str
    token_type: str = "bearer"


@dataclass(frozen=True)
class VerifyEmailCommand:
    email: str
    otp: str


@dataclass(frozen=True)
class VerifyEmailResult:
    email: str
    message: str


@dataclass(frozen=True)
class ResendVerificationCommand:
    email: str


@dataclass(frozen=True)
class ResendVerificationResult:
    email: str
    message: str


@dataclass(frozen=True)
class LogoutCommand:
    token_payload: dict[str, object]


@dataclass(frozen=True)
class LogoutResult:
    message: str


@dataclass(frozen=True)
class ForgotPasswordCommand:
    email: str


@dataclass(frozen=True)
class ForgotPasswordResult:
    message: str
