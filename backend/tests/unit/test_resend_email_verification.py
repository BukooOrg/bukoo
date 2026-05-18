from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.dtos.auth_dto import (
    ResendVerificationCommand,
    ResendVerificationResult,
)
from app.application.interfaces import IEmailNotificationService, IPasswordHasher
from app.application.use_cases.auth.resend_email_verification import (
    ResendEmailVerificationUseCase,
)
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions import UserAlreadyVerifiedError, UserNotFoundError
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
    def __init__(self) -> None:
        self.saved: list[VerificationTokenEntity] = []

    @override
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
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


def _make_pending_user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id="user-id-1",
        _email=_EMAIL,
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=UserStatus.PENDING,
        _hashed_password="hashed:secret",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_active_user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id="user-id-1",
        _email=_EMAIL,
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed:secret",
        _avatar_url=None,
        _last_login_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_use_case(
    user: UserEntity | None,
    db_session: AsyncMock | None = None,
    email_svc: IEmailNotificationService | None = None,
) -> tuple[ResendEmailVerificationUseCase, FakeVerificationTokenRepository]:
    if db_session is None:
        db_session = AsyncMock()
    if email_svc is None:
        email_svc = MagicMock(spec=IEmailNotificationService)
    token_repo = FakeVerificationTokenRepository()
    use_case = ResendEmailVerificationUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        verification_token_repo=token_repo,
        hasher=FakePasswordHasher(),
        email_svc=email_svc,
    )
    return use_case, token_repo


@pytest.mark.unit
class TestResendEmailVerificationUseCase:
    async def test_returns_result_with_correct_email_and_message(self) -> None:
        user = _make_pending_user()
        use_case, _ = _make_use_case(user=user)

        result = await use_case.execute(ResendVerificationCommand(email=_EMAIL))

        assert isinstance(result, ResendVerificationResult)
        assert result.email == _EMAIL
        assert result.message == "Verification email resent successfully"

    async def test_new_verification_token_is_persisted(self) -> None:
        user = _make_pending_user()
        use_case, token_repo = _make_use_case(user=user)

        await use_case.execute(ResendVerificationCommand(email=_EMAIL))

        assert len(token_repo.saved) == 1
        saved = token_repo.saved[0]
        assert saved.user_id == user.id
        assert saved.type == VerificationTokenType.EMAIL_VERIFY

    async def test_new_token_persisted_even_when_prior_token_exists(self) -> None:
        user = _make_pending_user()
        use_case, token_repo = _make_use_case(user=user)

        await use_case.execute(ResendVerificationCommand(email=_EMAIL))
        await use_case.execute(ResendVerificationCommand(email=_EMAIL))

        assert len(token_repo.saved) == 2

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        user = _make_pending_user()
        use_case, _ = _make_use_case(user=user, db_session=db_session)

        await use_case.execute(ResendVerificationCommand(email=_EMAIL))

        db_session.commit.assert_called_once()

    async def test_email_service_called_with_correct_recipient(self) -> None:
        email_svc = MagicMock(spec=IEmailNotificationService)
        user = _make_pending_user()
        use_case, _ = _make_use_case(user=user, email_svc=email_svc)

        await use_case.execute(ResendVerificationCommand(email=_EMAIL))

        email_svc.send_verification_email.assert_called_once()
        call_kwargs = email_svc.send_verification_email.call_args
        assert call_kwargs.kwargs["to"] == _EMAIL
        assert call_kwargs.kwargs["otp"].isdigit()
        assert len(call_kwargs.kwargs["otp"]) == 6

    async def test_raises_user_not_found_when_email_unknown(self) -> None:
        use_case, _ = _make_use_case(user=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(ResendVerificationCommand(email="ghost@example.com"))

    async def test_raises_user_already_verified_when_status_active(self) -> None:
        user = _make_active_user()
        use_case, _ = _make_use_case(user=user)

        with pytest.raises(UserAlreadyVerifiedError):
            await use_case.execute(ResendVerificationCommand(email=_EMAIL))
