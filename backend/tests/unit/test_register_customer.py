from __future__ import annotations

from datetime import date, timedelta
from typing import override
from unittest.mock import AsyncMock

import pytest
from pydantic import ValidationError

from app.application.dtos.auth_dto import RegisterCommand, RegisterResult
from app.application.interfaces import IEmailNotificationService, IPasswordHasher
from app.application.use_cases.auth.register_customer import RegisterCustomerUseCase
from app.core.constants import UserRole, UserStatus, VerificationTokenType
from app.domain.entities.user_entity import UserEntity
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.exceptions import UserAlreadyExistsError
from app.domain.repositories import IUserRepository, IVerificationTokenRepository
from app.presentation.schemas.auth_schema import RegisterRequest


class FakeUserRepository(IUserRepository):
    def __init__(self, email_exists: bool = False) -> None:
        self._email_exists = email_exists
        self.saved: list[UserEntity] = []

    @override
    async def exists_by_email(self, email: str) -> bool:
        return self._email_exists

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
    async def find_by_email(self, email: str) -> UserEntity | None:
        return None

    @override
    async def soft_delete(self, user_id: str) -> None:
        pass

    @override
    async def count_including_deleted(self) -> int:
        return 0


class FakeVerificationTokenRepository(IVerificationTokenRepository):
    def __init__(self) -> None:
        self.saved: list[VerificationTokenEntity] = []

    @override
    async def save(self, token: VerificationTokenEntity) -> None:
        self.saved.append(token)

    @override
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
        return None


class FakePasswordHasher(IPasswordHasher):
    @override
    def hash(self, value: str) -> str:
        return f"hashed:{value}"

    @override
    def verify(self, plain: str, hashed: str) -> bool:
        return hashed == f"hashed:{plain}"


class FakeEmailNotificationService(IEmailNotificationService):
    def __init__(self) -> None:
        self.sent_verification_emails: list[dict[str, str]] = []
        self.sent_welcome_emails: list[dict[str, str]] = []

    @override
    def send_welcome(self, to: str, full_name: str) -> None:
        self.sent_welcome_emails.append({"to": to, "full_name": full_name})

    @override
    def send_verification_email(self, to: str, otp: str) -> None:
        self.sent_verification_emails.append({"to": to, "otp": otp})


def _make_valid_command(
    email: str = "reader@example.com",
    password: str = "Secure@123",
    full_name: str = "Ada Lovelace",
    date_of_birth: date = date(1990, 5, 15),
) -> RegisterCommand:
    return RegisterCommand(
        email=email,
        password=password,
        full_name=full_name,
        date_of_birth=date_of_birth,
    )


@pytest.mark.unit
class TestRegisterCustomerUseCase:
    async def test_returns_register_result_with_pending_status(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        result = await use_case.execute(_make_valid_command())

        assert isinstance(result, RegisterResult)
        assert result.status == UserStatus.PENDING
        assert result.email == "reader@example.com"
        assert result.full_name == "Ada Lovelace"

    async def test_user_repo_save_called_with_correct_role_and_status(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        await use_case.execute(_make_valid_command())

        assert len(user_repo.saved) == 1
        saved_user = user_repo.saved[0]
        assert saved_user.role == UserRole.USER
        assert saved_user.status == UserStatus.PENDING

    async def test_verification_token_saved_with_email_verify_type(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        await use_case.execute(_make_valid_command())

        assert len(token_repo.saved) == 1
        saved_token = token_repo.saved[0]
        assert saved_token.type == VerificationTokenType.EMAIL_VERIFY

    async def test_db_session_commit_called_once(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        await use_case.execute(_make_valid_command())

        db_session.commit.assert_called_once()

    async def test_verification_email_sent_to_correct_address(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        await use_case.execute(_make_valid_command(email="reader@example.com"))

        assert len(email_svc.sent_verification_emails) == 1
        assert email_svc.sent_verification_emails[0]["to"] == "reader@example.com"

    async def test_raises_user_already_exists_error_when_email_taken(self) -> None:
        db_session = AsyncMock()
        user_repo = FakeUserRepository(email_exists=True)
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )

        with pytest.raises(UserAlreadyExistsError):
            await use_case.execute(_make_valid_command())

    async def test_user_aged_exactly_5_years_is_accepted(self) -> None:
        """Boundary: user who turns 5 exactly today is accepted by the validator."""
        today = date.today()
        dob = date(today.year - 5, today.month, today.day)

        db_session = AsyncMock()
        user_repo = FakeUserRepository()
        token_repo = FakeVerificationTokenRepository()
        hasher = FakePasswordHasher()
        email_svc = FakeEmailNotificationService()

        use_case = RegisterCustomerUseCase(
            db_session=db_session,
            user_repo=user_repo,
            verification_token_repo=token_repo,
            hasher=hasher,
            email_svc=email_svc,
        )
        result = await use_case.execute(_make_valid_command(date_of_birth=dob))

        assert result.status == UserStatus.PENDING


@pytest.mark.unit
class TestRegisterRequestValidation:
    def test_user_aged_4_years_364_days_is_rejected(self) -> None:
        """Boundary: user who turns 5 tomorrow is rejected by the schema validator."""
        today = date.today()
        dob = date(today.year - 5, today.month, today.day) + timedelta(days=1)

        with pytest.raises(ValidationError):
            RegisterRequest(
                email="reader@example.com",
                password="Secure@123",
                full_name="Ada Lovelace",
                date_of_birth=dob,
            )

    def test_password_exactly_8_chars_with_all_required_types_is_accepted(
        self,
    ) -> None:
        """Boundary: minimum-length password satisfying all character requirements is accepted."""
        req = RegisterRequest(
            email="reader@example.com",
            password="Secure@1",
            full_name="Ada Lovelace",
            date_of_birth=date(1990, 5, 15),
        )

        assert req.password == "Secure@1"
