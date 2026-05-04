from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal, override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.auth_dto import LogoutCommand, LogoutResult
from app.application.interfaces.token_service import ITokenService
from app.application.use_cases.auth.logout import LogoutUseCase


class FakeTokenService(ITokenService):
    def __init__(self) -> None:
        self.revoked_token_payloads: list[dict[str, object]] = []
        self.revoked_jtis: set[str] = set()

    @override
    def create_access_token(self, subject: str) -> str:
        return f"token-for-{subject}"

    @override
    def decode_token(self, token: str) -> dict[str, object]:
        return {}

    @override
    async def revoke_token(self, payload: dict[str, object]) -> None:
        self.revoked_token_payloads.append(payload)

    @override
    async def is_token_revoked(self, jti: str) -> bool:
        return jti in self.revoked_jtis


def _make_token_payload(
    variant: Literal["expired", "legacy"] | None = None,
) -> dict[str, object]:
    token_payload = {
        "sub": "user-id",
        "exp": datetime.now(UTC),
        "type": "access",
        "jti": "uuidV4",
    }

    if variant in {"expired", "legacy"}:
        token_payload.setdefault("exp", datetime.now(UTC) - timedelta(minutes=15))

    return token_payload


_LOG_OUT_SUCCESS_MESSAGE = "Logged out successfully."


@pytest.mark.unit
class TestLogoutUseCase:
    async def test_returns_logout_result_with_success_message(self) -> None:
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)

        result = await use_case.execute(
            LogoutCommand(token_payload=_make_token_payload())
        )

        assert isinstance(result, LogoutResult)
        assert result.message == _LOG_OUT_SUCCESS_MESSAGE

    async def test_revoke_token_called_with_correct_token(self) -> None:
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)
        expected_payload = _make_token_payload()

        await use_case.execute(LogoutCommand(token_payload=expected_payload))

        assert token_svc.revoked_token_payloads == [expected_payload]

    async def test_revoke_token_called_exactly_once(self) -> None:
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)

        await use_case.execute(LogoutCommand(token_payload=_make_token_payload()))

        assert len(token_svc.revoked_token_payloads) == 1

    async def test_db_session_commit_not_called(self) -> None:
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)

        await use_case.execute(LogoutCommand(token_payload=_make_token_payload()))

        db_session.commit.assert_not_called()

    async def test_already_expired_token_does_not_raise(self) -> None:
        """revoke_token on an expired token must not raise — JWTService skips the write."""
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)

        result = await use_case.execute(
            LogoutCommand(token_payload=_make_token_payload(variant="expired"))
        )

        assert result.message == _LOG_OUT_SUCCESS_MESSAGE

    async def test_token_without_jti_does_not_raise(self) -> None:
        """revoke_token on a legacy token (no jti) must not raise."""
        db_session = AsyncMock()
        token_svc = FakeTokenService()
        use_case = LogoutUseCase(db_session=db_session, token_svc=token_svc)

        result = await use_case.execute(
            LogoutCommand(token_payload=_make_token_payload(variant="legacy"))
        )

        assert result.message == _LOG_OUT_SUCCESS_MESSAGE
