from __future__ import annotations

from typing import override

from app.application.dtos.auth_dto import AuthResult
from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import UserStatus
from app.domain.exceptions import (
    InvalidCredentialsError,
    UserNotVerifiedError,
    UserSuspendedError,
)
from app.domain.repositories.user_repository import IUserRepository


class CredentialAuthProvider(IAuthProvider):
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

        user = await self._user_repo.find_by_email(email)

        if user is None or not user.have_password:
            raise InvalidCredentialsError()

        assert user.hashed_password is not None
        if not self._hasher.verify(password, user.hashed_password):
            raise InvalidCredentialsError()

        if user.status == UserStatus.PENDING:
            raise UserNotVerifiedError(user.email)

        if user.status == UserStatus.SUSPENDED:
            raise UserSuspendedError(user.email)

        user.record_login()
        await self._user_repo.save(user)

        return AuthResult(user_id=user.id, email=user.email, is_new_user=False)
