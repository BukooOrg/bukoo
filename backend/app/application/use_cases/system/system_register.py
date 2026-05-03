"""
SystemRegisterUseCase — creates a new admin user.

This is only called once on the app setup. No need email verification.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.interfaces.password_hasher import IPasswordHasher
from app.core.config import get_configs
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.domain.entities import AccountEntity, UserEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories import IAccountRepository, IUserRepository

from ..base import BaseUseCase

logger = structlog.get_logger(__name__)


class SystemRegisterUseCase(BaseUseCase):
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

    async def execute(self) -> None:
        logger.info("Creating system admin user...")

        configs = get_configs()
        email = configs.DEFAULT_ADMIN_MAIL
        full_name = configs.DEFAULT_ADMIN_FULL_NAME
        password = configs.DEFAULT_ADMIN_PASSWORD

        if await self._user_repo.exists_by_email(email):
            raise UserAlreadyExistsError(email)

        now = datetime.now(UTC)

        user = UserEntity(
            _id=str(uuid7()),
            _email=email,
            _full_name=full_name,
            _date_of_birth=date.today(),
            _role=UserRole.ADMIN,
            _status=UserStatus.ACTIVE,  # no need email verification
            _hashed_password=self._hasher.hash(password),
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

        logger.info("System admin user is created successfully!")
        logger.info(
            "System admin details", email=email, full_name=full_name, password=password
        )
