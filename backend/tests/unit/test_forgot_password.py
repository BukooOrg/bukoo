from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.auth_dto import ForgotPasswordCommand, ForgotPasswordResult
from app.application.interfaces import IEmailNotificationService, IPasswordHasher
from app.application.use_cases.auth.forgot_password import ForgotPasswordUseCase
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.repositories import IUserRepository, IVerificationTokenRepository


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        if self._user and self._user.email == email:
            return self._user
        return None

    @override
    async def save(self, user: UserEntity) -> None:
        pass

    @override
    async def find_by_id(self, user_id: str) -> UserEntity | None:
        return None

    @override
    async def find_by_id_including_deleted(self, user_id: str) -> UserEntity | None:
        return None

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


class FakeVerificationTokenRepository(IVerificationTokenRepository):
    def __init__(self, existing_token: VerificationTokenEntity | None = None) -> None:
        self._existing_token = existing_token
        self.saved: list[VerificationTokenEntity] = []

    @override
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
        if (
            self._existing_token is not None
            and self._existing_token.user_id == user_id
            and self._existing_token.type == token_type
        ):
            return self._existing_token
        return None

    @override
    async def save(self, token: VerificationTokenEntity) -> None:
        self.saved.append(token)


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


_EMAIL = "reader@example.com"


def _make_user(status: UserStatus = UserStatus.ACTIVE) -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id="user-id-1",
        _email=_EMAIL,
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=status,
        _hashed_password="hashed:secret",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_existing_token(user_id: str) -> VerificationTokenEntity:
    now = datetime.now(UTC)
    return VerificationTokenEntity(
        _id="token-id-1",
        _user_id=user_id,
        _token_hash="hashed:123456",
        _type=VerificationTokenType.PASSWORD_RESET,
        _expires_at=now,
        _created_at=now,
        _updated_at=now,
    )


def _make_use_case(
    user: UserEntity | None,
    existing_token: VerificationTokenEntity | None = None,
    db_session: AsyncMock | None = None,
    email_svc: IEmailNotificationService | None = None,
) -> tuple[ForgotPasswordUseCase, FakeVerificationTokenRepository]:
    if db_session is None:
        db_session = AsyncMock()
    if email_svc is None:
        email_svc = MagicMock(spec=IEmailNotificationService)
    token_repo = FakeVerificationTokenRepository(existing_token=existing_token)
    use_case = ForgotPasswordUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        verification_token_repo=token_repo,
        hasher=FakePasswordHasher(),
        email_svc=email_svc,
    )
    return use_case, token_repo


@pytest.mark.unit
class TestForgotPasswordUseCase:
    async def test_returns_generic_message_for_active_user(self) -> None:
        user = _make_user(UserStatus.ACTIVE)
        use_case, _ = _make_use_case(user=user)

        result = await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert isinstance(result, ForgotPasswordResult)
        assert isinstance(result.message, str)

    async def test_new_reset_token_is_persisted(self) -> None:
        user = _make_user(UserStatus.ACTIVE)
        use_case, token_repo = _make_use_case(user=user)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert len(token_repo.saved) == 1
        saved = token_repo.saved[0]
        assert saved.user_id == user.id
        assert saved.type == VerificationTokenType.PASSWORD_RESET

    async def test_reset_token_expires_in_15_minutes(self) -> None:
        user = _make_user(UserStatus.ACTIVE)
        use_case, token_repo = _make_use_case(user=user)
        before = datetime.now(UTC)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        saved = token_repo.saved[0]
        delta = saved.expires_at - before
        tolerance = 5

        assert 14 * 60 < delta.total_seconds() <= 15 * 60 + tolerance

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        user = _make_user(UserStatus.ACTIVE)
        use_case, _ = _make_use_case(user=user, db_session=db_session)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        db_session.commit.assert_called_once()

    async def test_email_service_called_with_correct_recipient(self) -> None:
        email_svc = MagicMock(spec=IEmailNotificationService)
        user = _make_user(UserStatus.ACTIVE)
        use_case, _ = _make_use_case(user=user, email_svc=email_svc)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        email_svc.send_password_reset_email.assert_called_once()
        call_kwargs = email_svc.send_password_reset_email.call_args
        assert call_kwargs.kwargs["to"] == _EMAIL
        assert call_kwargs.kwargs["otp"].isdigit()
        assert len(call_kwargs.kwargs["otp"]) == 6

    async def test_existing_active_token_is_invalidated(self) -> None:
        user = _make_user(UserStatus.ACTIVE)
        existing = _make_existing_token(user.id)
        use_case, token_repo = _make_use_case(user=user, existing_token=existing)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert existing.is_used
        assert len(token_repo.saved) == 2  # invalidated old + new token

    async def test_no_existing_token_creates_only_one_new_token(self) -> None:
        user = _make_user(UserStatus.ACTIVE)
        use_case, token_repo = _make_use_case(user=user, existing_token=None)

        await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert len(token_repo.saved) == 1

    async def test_silently_succeeds_when_user_not_found(self) -> None:
        email_svc = MagicMock(spec=IEmailNotificationService)
        use_case, token_repo = _make_use_case(user=None, email_svc=email_svc)

        result = await use_case.execute(
            ForgotPasswordCommand(email="ghost@example.com")
        )

        assert isinstance(result, ForgotPasswordResult)
        email_svc.send_password_reset_email.assert_not_called()
        assert len(token_repo.saved) == 0

    async def test_silently_succeeds_for_pending_user(self) -> None:
        email_svc = MagicMock(spec=IEmailNotificationService)
        user = _make_user(UserStatus.PENDING)
        use_case, token_repo = _make_use_case(user=user, email_svc=email_svc)

        result = await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert isinstance(result, ForgotPasswordResult)
        email_svc.send_password_reset_email.assert_not_called()
        assert len(token_repo.saved) == 0

    async def test_silently_succeeds_for_suspended_user(self) -> None:
        email_svc = MagicMock(spec=IEmailNotificationService)
        user = _make_user(UserStatus.SUSPENDED)
        use_case, token_repo = _make_use_case(user=user, email_svc=email_svc)

        result = await use_case.execute(ForgotPasswordCommand(email=_EMAIL))

        assert isinstance(result, ForgotPasswordResult)
        email_svc.send_password_reset_email.assert_not_called()
        assert len(token_repo.saved) == 0
