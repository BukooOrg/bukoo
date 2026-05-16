"""SQLAlchemy async implementation of IAddressRepository."""

from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.address_entity import AddressEntity
from app.domain.repositories.address_repository import IAddressRepository
from app.infrastructure.db.mappers.address_mapper import AddressMapper
from app.infrastructure.db.models import AddressModel


class AddressRepositoryImpl(IAddressRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_address_by_user_id(self, user_id: str) -> AddressEntity | None:
        stmt = select(AddressModel).where(AddressModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return AddressMapper.to_entity(model) if model else None

    @override
    async def save(self, address: AddressEntity) -> None:
        model = AddressMapper.to_model(address)
        model.id = address.id
        model.user_id = address.user_id

        await self._session.merge(model)
