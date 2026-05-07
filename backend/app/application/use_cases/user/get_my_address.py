from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.user_dto import GetMyAddressCommand, GetMyAddressResult
from app.domain.exceptions import AddressNotFoundError, UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class GetMyAddressUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, user_repo: IUserRepository) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo

    @override
    async def execute(self, command: GetMyAddressCommand) -> GetMyAddressResult:
        user = await self._user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        address = user.address
        if address is None:
            raise AddressNotFoundError(command.user_id)

        return GetMyAddressResult(
            id=address.id,
            user_id=address.user_id,
            recipient_name=address.recipient_name,
            phone=address.phone,
            address_line1=address.address_line1,
            address_line2=address.address_line2,
            city=address.city,
            state=address.state,
            postcode=address.postcode,
            country=address.country,
            created_at=address.created_at,
            updated_at=address.updated_at,
        )
