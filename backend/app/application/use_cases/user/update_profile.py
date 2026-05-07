from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import UpdateProfileCommand, UpdateProfileResult
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class UpdateProfileUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, user_repo: IUserRepository) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo

    @override
    async def execute(self, command: UpdateProfileCommand) -> UpdateProfileResult:
        user = await self._user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        user.update_profile(
            full_name=command.full_name,
            date_of_birth=command.date_of_birth,
        )

        await self._user_repo.save(user)
        await self._db_session.commit()

        return UpdateProfileResult(
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
