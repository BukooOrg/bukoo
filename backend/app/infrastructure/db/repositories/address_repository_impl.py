"""SQLAlchemy async implementation of IAddressRepository."""

from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.address_entity import AddressEntity
from app.domain.repositories.address_repository import IAddressRepository
from app.infrastructure.db.mappers.address_mapper import AddressMapper


class AddressRepositoryImpl(IAddressRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, address: AddressEntity) -> None:
        model = AddressMapper.to_model(address)
        model.id = address.id
        model.user_id = address.user_id

        await self._session.merge(model)
