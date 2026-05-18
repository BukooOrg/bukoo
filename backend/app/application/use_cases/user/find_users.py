from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import FindUserResult, FindUsersCommand
from app.core.query_params import PaginatedResult
from app.domain.repositories.user_repository import IUserRepository, UserFilters

from ..base import BaseUseCase


class FindUsersUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, user_repo: IUserRepository) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo

    @override
    async def execute(self, cmd: FindUsersCommand) -> PaginatedResult[FindUserResult]:
        filters = UserFilters(role=cmd.role, status=cmd.status)
        result = await self._user_repo.find_all(cmd.query_params, filters)
        return PaginatedResult(
            items=[
                FindUserResult(
                    id=u.id,
                    email=u.email,
                    full_name=u.full_name,
                    date_of_birth=u.date_of_birth,
                    role=u.role,
                    status=u.status,
                    avatar_url=u.avatar_url,
                    have_password=u.have_password,
                    last_login_at=u.last_login_at,
                    created_at=u.created_at,
                    updated_at=u.updated_at,
                )
                for u in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
