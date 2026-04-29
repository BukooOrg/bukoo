"""
CredentialProvider — Strategy pattern: email + password authentication.
Rejects soft-deleted users and PENDING (unverified) users.
"""

from __future__ import annotations

from typing import override

from app.application.dtos.auth_dto import AuthResult
from app.application.interfaces.auth_provider import IAuthStrategy
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import UserStatus
from app.domain.exceptions import InvalidCredentialsError, UserNotVerifiedError
from app.domain.repositories.user_repository import IUserRepository


class CredentialProvider(IAuthStrategy):
    def __init__(
        self,
        user_repo: IUserRepository,
        hasher: IPasswordHasher,
    ) -> None:
        self._user_repo = user_repo
        self._hasher = hasher

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        email = payload.get("email", "")
        password = payload.get("password", "")

        # find_by_email already excludes soft-deleted rows
        user = await self._user_repo.find_by_email(email)

        if user is None or not user.has_password:
            raise InvalidCredentialsError()

        if not self._hasher.verify(password, user.hashed_password):  # type: ignore[arg-type]
            raise InvalidCredentialsError()

        if user.status == UserStatus.PENDING:
            raise UserNotVerifiedError(user.email)

        user.record_login()
        await self._user_repo.save(user)

        return AuthResult(user_id=user.id, email=user.email, is_new_user=False)
