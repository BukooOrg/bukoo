from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import RemoveAvatarCommand, RemoveAvatarResult
from app.application.interfaces.storage_service import IStorageService
from app.application.use_cases.user.remove_avatar import RemoveAvatarUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.repositories.user_repository import IUserRepository


def _make_user(
    user_id: str = "user-001", avatar_url: str | None = "pub/avatars/user-001"
) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="user@example.com",
        _full_name="Jane Doe",
        _date_of_birth=date(1990, 6, 15),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed",
        _avatar_url=avatar_url,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._store: dict[str, UserEntity] = {}
        if user is not None:
            self._store[user.id] = user

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return self._store.get(user_id)

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        return next((u for u in self._store.values() if u.email == email), None)

    @override
    async def save(self, user: UserEntity) -> None:
        self._store[user.id] = user

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def exists_by_email(self, email: str) -> bool:
        return any(u.email == email for u in self._store.values())

    @override
    async def count_including_deleted(self) -> int:
        return len(self._store)

    async def find_all(self, query: object, filters: object) -> object:
        raise NotImplementedError


class FakeStorageService(IStorageService):
    def __init__(self) -> None:
        self.deleted_keys: list[str] = []

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        return f"http://minio:9000/bukoo/{key}"

    @override
    async def load_once(self, key: str) -> bytes:
        return b""

    @override
    def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        async def _gen() -> AsyncGenerator[bytes, None]:
            yield b""

        return _gen()

    @override
    async def exists(self, key: str) -> bool:
        return False

    @override
    async def delete(self, key: str) -> None:
        self.deleted_keys.append(key)

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"http://minio:9000/bukoo/{key}?expires={expires_in}"


@pytest.mark.unit
class TestRemoveAvatarUseCase:
    async def test_returns_result_with_avatar_url_none_when_user_has_avatar(
        self,
    ) -> None:
        user = _make_user(avatar_url="pub/avatars/user-001")
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = RemoveAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_svc=storage
        )

        result = await use_case.execute(RemoveAvatarCommand(user_id=user.id))

        assert isinstance(result, RemoveAvatarResult)
        assert result.avatar_url is None

    async def test_storage_delete_called_with_correct_key(self) -> None:
        avatar_key = "pub/avatars/user-001"
        user = _make_user(avatar_url=avatar_key)
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = RemoveAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_svc=storage
        )

        await use_case.execute(RemoveAvatarCommand(user_id=user.id))

        assert storage.deleted_keys == [avatar_key]

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        repo = FakeUserRepository()
        storage = FakeStorageService()
        use_case = RemoveAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_svc=storage
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(RemoveAvatarCommand(user_id="nonexistent-id"))

    async def test_no_storage_delete_when_avatar_already_none(self) -> None:
        user = _make_user(avatar_url=None)
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = RemoveAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_svc=storage
        )

        result = await use_case.execute(RemoveAvatarCommand(user_id=user.id))

        assert result.avatar_url is None
        assert storage.deleted_keys == []

    async def test_commit_before_storage_delete(self) -> None:
        user = _make_user(avatar_url="pub/avatars/user-001")
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        db_session = AsyncMock()
        call_order: list[str] = []

        original_commit = db_session.commit

        async def tracking_commit() -> None:
            call_order.append("commit")
            await original_commit()

        async def tracking_delete(key: str) -> None:
            call_order.append("delete")

        db_session.commit = tracking_commit
        storage.delete = tracking_delete

        use_case = RemoveAvatarUseCase(
            db_session=db_session, user_repo=repo, storage_svc=storage
        )

        await use_case.execute(RemoveAvatarCommand(user_id=user.id))

        assert call_order == ["commit", "delete"]
