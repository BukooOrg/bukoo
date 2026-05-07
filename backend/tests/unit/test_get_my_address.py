from __future__ import annotations

from datetime import UTC, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import GetMyAddressCommand, GetMyAddressResult
from app.application.use_cases.user.get_my_address import GetMyAddressUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.address_entity import AddressEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.address import AddressNotFoundError
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository


def _make_address() -> AddressEntity:
    now = datetime.now(UTC)
    return AddressEntity(
        _id="addr-01",
        _user_id="user-01",
        _recipient_name="Jane Doe",
        _phone="+60123456789",
        _address_line1="123 Jalan Bukit Bintang",
        _address_line2="Level 5",
        _city="Kuala Lumpur",
        _state="Wilayah Persekutuan",
        _postcode="50200",
        _country="Malaysia",
        _created_at=now,
        _updated_at=now,
    )


def _make_user(*, address: AddressEntity | None = None) -> UserEntity:
    return UserEntity(
        _id="user-01",
        _email="test@example.com",
        _full_name="Test User",
        _date_of_birth=None,
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=datetime.now(UTC),
        _updated_at=datetime.now(UTC),
        _deleted_at=None,
        _address=address,
    )


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._user if (self._user and self._user.id == user_id) else None

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    @override
    async def save(self, user: UserEntity) -> None:
        pass

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def exists_by_email(self, email: str) -> bool:
        return False

    @override
    async def count_including_deleted(self) -> int:
        return 0


@pytest.mark.unit
class TestGetMyAddressUseCase:
    async def test_returns_result_when_address_exists(self) -> None:
        address = _make_address()
        user = _make_user(address=address)
        use_case = GetMyAddressUseCase(
            db_session=AsyncMock(),
            user_repo=FakeUserRepository(user),
        )

        result = await use_case.execute(GetMyAddressCommand(user_id="user-01"))

        assert isinstance(result, GetMyAddressResult)
        assert result.id == "addr-01"
        assert result.user_id == "user-01"
        assert result.recipient_name == "Jane Doe"
        assert result.phone == "+60123456789"
        assert result.address_line1 == "123 Jalan Bukit Bintang"
        assert result.address_line2 == "Level 5"
        assert result.city == "Kuala Lumpur"
        assert result.state == "Wilayah Persekutuan"
        assert result.postcode == "50200"
        assert result.country == "Malaysia"
        assert result.created_at == address.created_at
        assert result.updated_at == address.updated_at

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        use_case = GetMyAddressUseCase(
            db_session=AsyncMock(),
            user_repo=FakeUserRepository(None),
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(GetMyAddressCommand(user_id="user-01"))

    async def test_raises_address_not_found_when_user_has_no_address(self) -> None:
        user = _make_user(address=None)
        use_case = GetMyAddressUseCase(
            db_session=AsyncMock(),
            user_repo=FakeUserRepository(user),
        )

        with pytest.raises(AddressNotFoundError):
            await use_case.execute(GetMyAddressCommand(user_id="user-01"))
