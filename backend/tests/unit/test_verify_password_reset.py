from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import (
    VerifyPasswordResetCommand,
    VerifyPasswordResetResult,
)
from app.application.interfaces import IPasswordHasher
from app.application.use_cases.auth.verify_password_reset import (
    VerifyPasswordResetUseCase,
)
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions.auth import InvalidTokenError
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


class FakeVerificationTokenRepository(IVerificationTokenRepository):
    def __init__(self, token: VerificationTokenEntity | None = None) -> None:
        self._token = token

    @override
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
        if (
            self._token is not None
            and self._token.user_id == user_id
            and self._token.type == token_type
        ):
            return self._token
        return None

    @override
    async def save(self, token: VerificationTokenEntity) -> None:
        pass


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


_EMAIL = "reader@example.com"
_OTP = "123456"


def _make_user() -> UserEntity:
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


def _make_token(user_id: str, otp: str = _OTP) -> VerificationTokenEntity:
    now = datetime.now(UTC)
    return VerificationTokenEntity(
        _id="token-id-1",
        _user_id=user_id,
        _token_hash=f"hashed:{otp}",
        _type=VerificationTokenType.PASSWORD_RESET,
        _expires_at=now + timedelta(minutes=15),
        _created_at=now,
        _updated_at=now,
    )


def _make_use_case(
    user: UserEntity | None,
    token: VerificationTokenEntity | None = None,
) -> VerifyPasswordResetUseCase:
    return VerifyPasswordResetUseCase(
        db_session=AsyncMock(),
        user_repo=FakeUserRepository(user=user),
        verification_token_repo=FakeVerificationTokenRepository(token=token),
        hasher=FakePasswordHasher(),
    )


@pytest.mark.unit
class TestVerifyPasswordResetUseCase:
    async def test_returns_valid_true_for_correct_otp(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        use_case = _make_use_case(user=user, token=token)

        result = await use_case.execute(
            VerifyPasswordResetCommand(email=_EMAIL, otp=_OTP)
        )

        assert isinstance(result, VerifyPasswordResetResult)
        assert result.valid is True

    async def test_raises_invalid_token_when_user_not_found(self) -> None:
        use_case = _make_use_case(user=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                VerifyPasswordResetCommand(email="ghost@example.com", otp=_OTP)
            )

    async def test_raises_invalid_token_when_no_active_reset_token(self) -> None:
        user = _make_user()
        use_case = _make_use_case(user=user, token=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(VerifyPasswordResetCommand(email=_EMAIL, otp=_OTP))

    async def test_raises_invalid_token_when_otp_mismatch(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        use_case = _make_use_case(user=user, token=token)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                VerifyPasswordResetCommand(email=_EMAIL, otp="000000")
            )

    async def test_raises_invalid_token_for_wrong_token_type(self) -> None:
        user = _make_user()
        now = datetime.now(UTC)
        # EMAIL_VERIFY token — won't be returned for PASSWORD_RESET lookup
        email_verify_token = VerificationTokenEntity(
            _id="token-id-2",
            _user_id=user.id,
            _token_hash=f"hashed:{_OTP}",
            _type=VerificationTokenType.EMAIL_VERIFY,
            _expires_at=now + timedelta(minutes=15),
            _created_at=now,
            _updated_at=now,
        )
        use_case = _make_use_case(user=user, token=email_verify_token)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(VerifyPasswordResetCommand(email=_EMAIL, otp=_OTP))

    async def test_no_commit_called(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        db_session = AsyncMock()
        use_case = VerifyPasswordResetUseCase(
            db_session=db_session,
            user_repo=FakeUserRepository(user=user),
            verification_token_repo=FakeVerificationTokenRepository(token=token),
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(VerifyPasswordResetCommand(email=_EMAIL, otp=_OTP))

        db_session.commit.assert_not_called()
