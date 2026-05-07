from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import UpdateAvatarCommand, UpdateAvatarResult
from app.application.interfaces.storage_service import IStorageService
from app.application.use_cases.user.update_avatar import UpdateAvatarUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions.auth import UserNotFoundError
from app.domain.exceptions.storage import StorageUploadError
from app.domain.repositories.user_repository import IUserRepository


def _make_user(user_id: str = "user-001") -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id=user_id,
        _email="user@example.com",
        _full_name="Jane Doe",
        _date_of_birth=date(1990, 6, 15),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed",
        _avatar_url=None,
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


class FakeStorageService(IStorageService):
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.uploaded_key: str | None = None
        self.uploaded_content_type: str | None = None

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        if self._should_fail:
            raise StorageUploadError(key, "test failure")
        self.uploaded_key = key
        self.uploaded_content_type = content_type
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
        pass

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"http://minio:9000/bukoo/{key}?expires={expires_in}"


@pytest.mark.unit
class TestUpdateAvatarUseCase:
    async def test_returns_result_with_correct_avatar_url(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )

        result = await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        assert isinstance(result, UpdateAvatarResult)
        assert result.avatar_url == f"pub/avatars/{user.id}"

    async def test_updated_at_is_bumped(self) -> None:
        user = _make_user()
        original_updated_at = user.updated_at
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )

        result = await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        assert result.updated_at >= original_updated_at

    async def test_storage_upload_receives_correct_key_and_content_type(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )

        await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        assert storage.uploaded_key == f"pub/avatars/{user.id}"
        assert storage.uploaded_content_type == "image/jpeg"

    async def test_commit_called_once(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        db_session = AsyncMock()
        use_case = UpdateAvatarUseCase(
            db_session=db_session, user_repo=repo, storage_service=storage
        )

        await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_user_missing(self) -> None:
        repo = FakeUserRepository()  # empty store
        storage = FakeStorageService()
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                UpdateAvatarCommand(
                    user_id="nonexistent-id",
                    file_data=b"fake image bytes",
                    content_type="image/jpeg",
                )
            )

    async def test_raises_storage_upload_error_on_upload_failure(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        storage = FakeStorageService(should_fail=True)
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )

        with pytest.raises(StorageUploadError):
            await use_case.execute(
                UpdateAvatarCommand(
                    user_id=user.id,
                    file_data=b"fake image bytes",
                    content_type="image/jpeg",
                )
            )

    async def test_second_upload_uses_same_key(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        storage = FakeStorageService()
        use_case = UpdateAvatarUseCase(
            db_session=AsyncMock(), user_repo=repo, storage_service=storage
        )
        expected_key = f"pub/avatars/{user.id}"

        await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"first image",
                content_type="image/jpeg",
            )
        )
        result = await use_case.execute(
            UpdateAvatarCommand(
                user_id=user.id,
                file_data=b"second image",
                content_type="image/png",
            )
        )

        assert result.avatar_url == expected_key
        assert storage.uploaded_key == expected_key
