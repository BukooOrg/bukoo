from __future__ import annotations

from datetime import UTC, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import UpsertAddressCommand, UpsertAddressResult
from app.application.use_cases.user.upsert_address import UpsertAddressUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.address_entity import AddressEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.address_repository import IAddressRepository
from app.domain.repositories.user_repository import IUserRepository


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


def _make_address() -> AddressEntity:
    now = datetime.now(UTC)
    return AddressEntity(
        _id="addr-01",
        _user_id="user-01",
        _recipient_name="Original Name",
        _phone="+60100000000",
        _address_line1="1 Old Road",
        _address_line2=None,
        _city="Old City",
        _state="Old State",
        _postcode="10000",
        _country="Malaysia",
        _created_at=now,
        _updated_at=now,
    )


def _make_command(**overrides: object) -> UpsertAddressCommand:
    base: dict[str, object] = {
        "user_id": "user-01",
        "recipient_name": "Jane Doe",
        "phone": "+60123456789",
        "address_line1": "12 Jalan Bukit Bintang",
        "address_line2": "Unit 5A",
        "city": "Kuala Lumpur",
        "state": "Wilayah Persekutuan",
        "postcode": "55100",
        "country": "Malaysia",
    }
    base.update(overrides)
    return UpsertAddressCommand(**base)  # type: ignore[arg-type]


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

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


class FakeAddressRepository(IAddressRepository):
    def __init__(self) -> None:
        self.saved: AddressEntity | None = None

    @override
    async def save(self, address: AddressEntity) -> None:
        self.saved = address

    @override
    async def find_address_by_user_id(self, user_id: str) -> AddressEntity | None:
        return None


@pytest.mark.unit
class TestUpsertAddressUseCase:
    async def test_creates_new_address_when_user_has_none(self) -> None:
        user = _make_user(address=None)
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=FakeAddressRepository(),
        )

        result = await use_case.execute(_make_command())

        assert isinstance(result, UpsertAddressResult)
        assert result.user_id == "user-01"
        assert result.recipient_name == "Jane Doe"
        assert result.phone == "+60123456789"
        assert result.address_line1 == "12 Jalan Bukit Bintang"
        assert result.address_line2 == "Unit 5A"
        assert result.city == "Kuala Lumpur"
        assert result.country == "Malaysia"

    async def test_updates_existing_address(self) -> None:
        original_address = _make_address()
        original_created_at = original_address.created_at
        user = _make_user(address=original_address)
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=FakeAddressRepository(),
        )

        result = await use_case.execute(_make_command())

        assert result.id == "addr-01"
        assert result.recipient_name == "Jane Doe"
        assert result.city == "Kuala Lumpur"
        assert result.created_at == original_created_at

    async def test_update_branch_preserves_id(self) -> None:
        original_address = _make_address()
        user = _make_user(address=original_address)
        db_session = AsyncMock()
        address_repo = FakeAddressRepository()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=address_repo,
        )

        result = await use_case.execute(_make_command())

        assert result.id == original_address.id
        assert address_repo.saved is not None
        assert address_repo.saved.id == original_address.id

    async def test_create_branch_calls_address_repo_save(self) -> None:
        user = _make_user(address=None)
        db_session = AsyncMock()
        address_repo = FakeAddressRepository()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=address_repo,
        )

        await use_case.execute(_make_command())

        assert address_repo.saved is not None

    async def test_commit_called_once(self) -> None:
        user = _make_user(address=None)
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=FakeAddressRepository(),
        )

        await use_case.execute(_make_command())

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(None),
            address_repo=FakeAddressRepository(),
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(_make_command())

    async def test_address_line2_none_is_accepted(self) -> None:
        user = _make_user(address=None)
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=FakeAddressRepository(),
        )

        result = await use_case.execute(_make_command(address_line2=None))

        assert result.address_line2 is None

    async def test_second_upsert_returns_updated_values(self) -> None:
        original_address = _make_address()
        user = _make_user(address=original_address)
        db_session = AsyncMock()
        use_case = UpsertAddressUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user),
            address_repo=FakeAddressRepository(),
        )

        await use_case.execute(_make_command(city="First City"))
        result = await use_case.execute(_make_command(city="Second City"))

        assert result.city == "Second City"
