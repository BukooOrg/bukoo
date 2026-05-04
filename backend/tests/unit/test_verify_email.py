from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import VerifyEmailCommand, VerifyEmailResult
from app.application.interfaces import IPasswordHasher
from app.application.use_cases.auth.verify_email import VerifyEmailUseCase
from app.core.constants import AuthProvider, UserRole, UserStatus, VerificationTokenType
from app.domain.entities.account_entity import AccountEntity
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions import (
    InvalidTokenError,
    UserAlreadyVerifiedError,
    UserNotFoundError,
)
from app.domain.repositories import IUserRepository, IVerificationTokenRepository
from app.domain.repositories.account_repository import IAccountRepository


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
            self._token
            and self._token.user_id == user_id
            and self._token.type == token_type
        ):
            return self._token
        return None

    @override
    async def save(self, token: VerificationTokenEntity) -> None:
        self.saved.append(token)


class FakeAccountRepository(IAccountRepository):
    def __init__(self) -> None:
        self.saved: list[AccountEntity] = []

    @override
    async def find_by_user_id(self, user_id: str) -> list[AccountEntity]:
        return []

    @override
    async def find_by_provider_and_open_id(
        self, provider: str, open_id: str
    ) -> AccountEntity | None:
        return None

    @override
    async def find_by_user_and_provider(
        self, user_id: str, provider: str
    ) -> AccountEntity | None:
        return None

    @override
    async def save(self, account: AccountEntity) -> None:
        self.saved.append(account)

    @override
    async def delete(self, account_id: str) -> None:
        pass


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


_OTP = "483920"
_EMAIL = "reader@example.com"


def _make_pending_user() -> UserEntity:
    now = datetime.now(UTC)
    from datetime import date

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
    from datetime import date

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
        _created_at=datetime.now(UTC),
        _updated_at=datetime.now(UTC),
        _deleted_at=None,
    )


def _make_token(user_id: str = "user-id-1", otp: str = _OTP) -> VerificationTokenEntity:
    now = datetime.now(UTC)
    hasher = FakePasswordHasher()
    return VerificationTokenEntity(
        _id="token-id-1",
        _user_id=user_id,
        _token_hash=hasher.hash(otp),
        _type=VerificationTokenType.EMAIL_VERIFY,
        _expires_at=now + timedelta(minutes=15),
        _created_at=now,
        _updated_at=now,
    )


def _make_use_case(
    user: UserEntity | None,
    token: VerificationTokenEntity | None,
    db_session: AsyncMock | None = None,
) -> tuple[VerifyEmailUseCase, FakeAccountRepository]:
    if db_session is None:
        db_session = AsyncMock()
    account_repo = FakeAccountRepository()
    use_case = VerifyEmailUseCase(
        db_session=db_session,
        user_repo=FakeUserRepository(user=user),
        verification_token_repo=FakeVerificationTokenRepository(token=token),
        account_repo=account_repo,
        hasher=FakePasswordHasher(),
    )
    return use_case, account_repo


def _valid_command(email: str = _EMAIL, otp: str = _OTP) -> VerifyEmailCommand:
    return VerifyEmailCommand(email=email, otp=otp)


@pytest.mark.unit
class TestVerifyEmailUseCase:
    async def test_returns_verify_email_result_with_correct_email(self) -> None:
        user = _make_pending_user()
        token = _make_token()
        use_case, _ = _make_use_case(user=user, token=token)

        result = await use_case.execute(_valid_command())

        assert isinstance(result, VerifyEmailResult)
        assert result.email == _EMAIL
        assert result.message == "Email verified successfully"

    async def test_user_status_transitions_to_active(self) -> None:
        user = _make_pending_user()
        token = _make_token()
        use_case, _ = _make_use_case(user=user, token=token)

        await use_case.execute(_valid_command())

        assert user.status == UserStatus.ACTIVE

    async def test_token_used_at_is_set_after_execution(self) -> None:
        user = _make_pending_user()
        token = _make_token()
        use_case, _ = _make_use_case(user=user, token=token)

        await use_case.execute(_valid_command())

        assert token.used_at is not None

    async def test_credential_account_is_saved(self) -> None:
        user = _make_pending_user()
        token = _make_token()
        use_case, account_repo = _make_use_case(user=user, token=token)

        await use_case.execute(_valid_command())

        assert len(account_repo.saved) == 1
        saved = account_repo.saved[0]
        assert saved.provider == AuthProvider.CREDENTIAL
        assert saved.user_id == user.id
        assert saved.open_id is None

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        user = _make_pending_user()
        token = _make_token()
        use_case, _ = _make_use_case(user=user, token=token, db_session=db_session)

        await use_case.execute(_valid_command())

        db_session.commit.assert_called_once()

    async def test_raises_user_not_found_when_email_unknown(self) -> None:
        use_case, _ = _make_use_case(user=None, token=None)

        with pytest.raises(UserNotFoundError):
            await use_case.execute(_valid_command(email="ghost@example.com"))

    async def test_raises_user_already_verified_when_status_active(self) -> None:
        user = _make_active_user()
        use_case, _ = _make_use_case(user=user, token=None)

        with pytest.raises(UserAlreadyVerifiedError):
            await use_case.execute(_valid_command())

    async def test_raises_invalid_token_when_no_active_token_exists(self) -> None:
        user = _make_pending_user()
        use_case, _ = _make_use_case(user=user, token=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(_valid_command())

    async def test_raises_invalid_token_when_otp_does_not_match(self) -> None:
        user = _make_pending_user()
        token = _make_token(otp=_OTP)
        use_case, _ = _make_use_case(user=user, token=token)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(_valid_command(otp="000000"))

    async def test_raises_invalid_token_when_token_already_consumed(self) -> None:
        user = _make_pending_user()
        token = _make_token()
        token.mark_used()
        use_case, _ = _make_use_case(user=user, token=None)

        with pytest.raises(InvalidTokenError):
            await use_case.execute(_valid_command())
