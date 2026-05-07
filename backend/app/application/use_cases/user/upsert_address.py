from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.user_dto import UpsertAddressCommand, UpsertAddressResult
from app.domain.entities.address_entity import AddressEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.address_repository import IAddressRepository
from app.domain.repositories.user_repository import IUserRepository

from ..base import BaseUseCase


class UpsertAddressUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        user_repo: IUserRepository,
        address_repo: IAddressRepository,
    ) -> None:
        super().__init__(db_session)
        self._user_repo = user_repo
        self._address_repo = address_repo

    @override
    async def execute(self, command: UpsertAddressCommand) -> UpsertAddressResult:
        user = await self._user_repo.find_by_id(command.user_id)
        if user is None:
            raise UserNotFoundError(command.user_id)

        if user.address is None:
            now = datetime.now(UTC)
            address = AddressEntity(
                _id=str(uuid7()),
                _user_id=user.id,
                _recipient_name=command.recipient_name,
                _phone=command.phone,
                _address_line1=command.address_line1,
                _address_line2=command.address_line2,
                _city=command.city,
                _state=command.state,
                _postcode=command.postcode,
                _country=command.country,
                _created_at=now,
                _updated_at=now,
            )
        else:
            address = user.address
            address.update(
                recipient_name=command.recipient_name,
                phone=command.phone,
                address_line1=command.address_line1,
                address_line2=command.address_line2,
                city=command.city,
                state=command.state,
                postcode=command.postcode,
                country=command.country,
            )

        await self._address_repo.save(address)
        await self._db_session.commit()

        return UpsertAddressResult(
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
