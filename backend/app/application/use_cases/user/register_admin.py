from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.user_dto import RegisterAdminCommand, RegisterAdminResult
from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.domain.entities.account_entity import AccountEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class RegisterAdminUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        hasher: IPasswordHasher,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._hasher = hasher

    @override
    async def execute(self, cmd: RegisterAdminCommand) -> RegisterAdminResult:
        if await self._user_repo.exists_by_email(cmd.email):
            raise UserAlreadyExistsError(cmd.email)

        now = datetime.now(UTC)
        hashed_password = self._hasher.hash(cmd.password)

        user = UserEntity(
            _id=str(uuid7()),
            _email=cmd.email,
            _full_name=cmd.full_name,
            _date_of_birth=cmd.date_of_birth,
            _role=UserRole.ADMIN,
            _status=UserStatus.ACTIVE,
            _hashed_password=hashed_password,
            _avatar_url=None,
            _last_login_at=None,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )
        await self._user_repo.save(user)

        account = AccountEntity(
            _id=str(uuid7()),
            _user_id=user.id,
            _provider=AuthProvider.CREDENTIAL,
            _open_id=None,
            _encrypted_token=None,
            _created_at=now,
            _updated_at=now,
        )
        await self._account_repo.save(account)
        await self._db_session.commit()

        return RegisterAdminResult(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            date_of_birth=user.date_of_birth,
            role=user.role,
            status=user.status,
            avatar_url=user.avatar_url,
            have_password=user.have_password,
            last_login_at=user.last_login_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
