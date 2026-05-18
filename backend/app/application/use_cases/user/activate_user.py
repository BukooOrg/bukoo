from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import ActivateUserCommand, ActivateUserResult
from app.core.constants import UserStatus
from app.domain.exceptions import UserNotFoundError
from app.domain.exceptions.user import (
    CannotActivatePendingUserError,
    UserAlreadyActiveError,
)
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class ActivateUserUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, user_repo: IUserRepository) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo

    @override
    async def execute(self, cmd: ActivateUserCommand) -> ActivateUserResult:
        user = await self._user_repo.find_by_id(cmd.user_id)
        if user is None:
            raise UserNotFoundError(cmd.user_id)

        if user.status == UserStatus.ACTIVE:
            raise UserAlreadyActiveError(user.id)

        if user.status == UserStatus.PENDING:
            raise CannotActivatePendingUserError()

        user.activate()
        await self._user_repo.save(user)
        await self._db_session.commit()

        return ActivateUserResult(
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
