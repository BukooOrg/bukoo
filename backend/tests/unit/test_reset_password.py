from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import ResetPasswordCommand, ResetPasswordResult
from app.application.interfaces import IPasswordHasher
from app.application.use_cases.auth.reset_password import ResetPasswordUseCase
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions.auth import InvalidTokenError
from app.domain.repositories import IUserRepository, IVerificationTokenRepository


class FakeUserRepository(IUserRepository):
    def __init__(self, user: UserEntity | None = None) -> None:
        self._user = user
        self.saved: list[UserEntity] = []

    @override
    async def find_by_email(self, email: str) -> UserEntity | None:
        if self._user and self._user.email == email:
            return self._user
        return None

    @override
    async def save(self, user: UserEntity) -> None:
        self.saved.append(user)

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
        self.saved: list[VerificationTokenEntity] = []

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
        self.saved.append(token)


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


_EMAIL = "reader@example.com"
_OTP = "482910"
_NEW_PASSWORD = "NewP@ssw0rd1!"


def _make_user() -> UserEntity:
    now = datetime.now(UTC)
    return UserEntity(
        _id="user-id-1",
        _email=_EMAIL,
        _full_name="Ada Lovelace",
        _date_of_birth=date(1990, 5, 15),
        _role=UserRole.USER,
        _status=UserStatus.ACTIVE,
        _hashed_password="hashed:old_password",
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
    token: VerificationTokenEntity | None,
    db_session: AsyncMock | None = None,
) -> ResetPasswordUseCase:
    if db_session is None:
        db_session = AsyncMock()
    return ResetPasswordUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        verification_token_repo=FakeVerificationTokenRepository(token=token),
        hasher=FakePasswordHasher(),
    )


@pytest.mark.unit
class TestResetPasswordUseCase:
    async def test_returns_success_message(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        use_case = _make_use_case(user=user, token=token)

        result = await use_case.execute(
            ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
        )

        assert isinstance(result, ResetPasswordResult)
        assert result.message == "Password has been reset successfully."

    async def test_user_password_is_updated(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        user_repo = FakeUserRepository(user=user)
        db_session = AsyncMock()
        use_case = ResetPasswordUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=FakeVerificationTokenRepository(token=token),
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(
            ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
        )

        assert user.hashed_password == f"hashed:{_NEW_PASSWORD}"
        assert len(user_repo.saved) == 1

    async def test_token_is_marked_used(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        token_repo = FakeVerificationTokenRepository(token=token)
        use_case = ResetPasswordUseCase(
            db_session=AsyncMock(),
            user_repo=FakeUserRepository(user=user),
            verification_token_repo=token_repo,
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(
            ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
        )

        assert token.is_used
        assert len(token_repo.saved) == 1

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        user = _make_user()
        token = _make_token(user.id)
        use_case = _make_use_case(user=user, token=token, db_session=db_session)

        await use_case.execute(
            ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
        )

        db_session.commit.assert_called_once()

    async def test_raises_invalid_token_when_user_not_found(self) -> None:
        use_case = _make_use_case(user=None, token=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                ResetPasswordCommand(
                    email="ghost@example.com", otp=_OTP, new_password=_NEW_PASSWORD
                )
            )

    async def test_raises_invalid_token_when_no_active_token(self) -> None:
        user = _make_user()
        use_case = _make_use_case(user=user, token=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
            )

    async def test_raises_invalid_token_when_otp_mismatch(self) -> None:
        user = _make_user()
        token = _make_token(user.id, otp="999999")
        use_case = _make_use_case(user=user, token=token)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(
                ResetPasswordCommand(
                    email=_EMAIL, otp="000000", new_password=_NEW_PASSWORD
                )
            )

    async def test_token_marked_used_even_when_same_password(self) -> None:
        user = _make_user()
        token = _make_token(user.id, otp="same_otp")
        token_repo = FakeVerificationTokenRepository(token=token)
        use_case = ResetPasswordUseCase(
            db_session=AsyncMock(),
            user_repo=FakeUserRepository(user=user),
            verification_token_repo=token_repo,
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(
            ResetPasswordCommand(
                email=_EMAIL, otp="same_otp", new_password=_NEW_PASSWORD
            )
        )

        assert token.is_used

    async def test_both_user_and_token_persisted_before_commit(self) -> None:
        user = _make_user()
        token = _make_token(user.id)
        user_repo = FakeUserRepository(user=user)
        token_repo = FakeVerificationTokenRepository(token=token)
        db_session = AsyncMock()

        call_order: list[str] = []
        original_user_save = user_repo.save
        original_token_save = token_repo.save
        original_commit = db_session.commit

        async def tracked_user_save(user: UserEntity) -> None:
            call_order.append("user_save")
            await original_user_save(user)

        async def tracked_token_save(token: VerificationTokenEntity) -> None:
            call_order.append("token_save")
            await original_token_save(token)

        async def tracked_commit() -> None:
            call_order.append("commit")
            await original_commit()

        user_repo.save = tracked_user_save
        token_repo.save = tracked_token_save
        db_session.commit = tracked_commit

        use_case = ResetPasswordUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=FakePasswordHasher(),
        )

        await use_case.execute(
            ResetPasswordCommand(email=_EMAIL, otp=_OTP, new_password=_NEW_PASSWORD)
        )

        assert call_order.index("user_save") < call_order.index("commit")
        assert call_order.index("token_save") < call_order.index("commit")
