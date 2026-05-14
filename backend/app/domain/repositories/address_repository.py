"""IAddressRepository — domain repository interface for AddressEntity."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.address_entity import AddressEntity


class IAddressRepository(ABC):
    @abstractmethod
    async def find_address_by_user_id(self, user_id: str) -> AddressEntity | None:
        pass

    @abstractmethod
    async def save(self, address: AddressEntity) -> None:
        pass
