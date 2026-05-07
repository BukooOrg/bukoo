from __future__ import annotations

from datetime import UTC, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.user_dto import SoftDeleteMeCommand, SoftDeleteMeResult
from app.application.use_cases.user.soft_delete_me import SoftDeleteMeUseCase
from app.core.constants import UserRole, UserStatus
from app.domain.entities.user_entity import UserEntity
from app.domain.exceptions import CustomerOnlyError, UserNotFoundError
from app.domain.repositories import IUserRepository

_DUMMY_PAYLOAD: dict[str, object] = {"sub": "test-user-id", "jti": "test-jti"}


def _make_user(
    user_id: str = "test-user-id", role: UserRole = UserRole.USER
) -> UserEntity:
    return UserEntity(
        _id=user_id,
        _email="user@example.com",
        _full_name="Test User",
        _date_of_birth=None,
        _role=role,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=datetime.now(UTC),
        _updated_at=datetime.now(UTC),
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


def _make_use_case(
    repo: FakeUserRepository,
    db_session: AsyncMock | None = None,
    token_svc: AsyncMock | None = None,
) -> SoftDeleteMeUseCase:
    return SoftDeleteMeUseCase(
        db_session=db_session or AsyncMock(),
        user_repo=repo,
        token_svc=token_svc or AsyncMock(),
    )


@pytest.mark.unit
class TestSoftDeleteMeUseCase:
    async def test_execute_returns_result_with_message(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        use_case = _make_use_case(repo)

        result = await use_case.execute(
            SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
        )

        assert isinstance(result, SoftDeleteMeResult)
        assert len(result.message) > 0

    async def test_execute_sets_deleted_at_and_is_deleted(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        use_case = _make_use_case(repo)

        await use_case.execute(
            SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
        )

        assert user.deleted_at is not None
        assert user.is_deleted is True

    async def test_execute_updates_updated_at(self) -> None:
        user = _make_user()
        original_updated_at = user.updated_at
        repo = FakeUserRepository(user)
        use_case = _make_use_case(repo)

        await use_case.execute(
            SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
        )

        assert user.updated_at >= original_updated_at

    async def test_execute_commits_before_revoking_token(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        db_session = AsyncMock()
        token_svc = AsyncMock()
        call_order: list[str] = []
        db_session.commit.side_effect = lambda: call_order.append("commit")
        token_svc.revoke_token.side_effect = lambda _: call_order.append("revoke")
        use_case = _make_use_case(repo, db_session=db_session, token_svc=token_svc)

        await use_case.execute(
            SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
        )

        assert call_order == ["commit", "revoke"]

    async def test_execute_revokes_token_with_payload(self) -> None:
        user = _make_user()
        repo = FakeUserRepository(user)
        token_svc = AsyncMock()
        use_case = _make_use_case(repo, token_svc=token_svc)

        await use_case.execute(
            SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
        )

        token_svc.revoke_token.assert_awaited_once_with(_DUMMY_PAYLOAD)

    async def test_raises_user_not_found_when_repo_returns_none(self) -> None:
        repo = FakeUserRepository()
        use_case = _make_use_case(repo)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(
                SoftDeleteMeCommand(
                    user_id="nonexistent-id", token_payload=_DUMMY_PAYLOAD
                )
            )

    async def test_raises_customer_only_error_when_user_is_admin(self) -> None:
        user = _make_user(role=UserRole.ADMIN)
        repo = FakeUserRepository(user)
        use_case = _make_use_case(repo)

        with pytest.raises(CustomerOnlyError):
            await use_case.execute(
                SoftDeleteMeCommand(user_id=user.id, token_payload=_DUMMY_PAYLOAD)
            )
