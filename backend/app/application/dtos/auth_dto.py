from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegisterCommand:
    email: str
    password: str
    full_name: str


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
