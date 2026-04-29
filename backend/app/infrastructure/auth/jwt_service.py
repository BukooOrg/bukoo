from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import override

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.application.interfaces.token_service import ITokenService
from app.core.config import get_configs
from app.domain.exceptions import InvalidTokenError, TokenExpiredError


class JWTService(ITokenService):
    @override
    def create_access_token(self, subject: str) -> str:
        configs = get_configs()
        expire = datetime.now(UTC) + timedelta(
            minutes=configs.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {"sub": subject, "exp": expire, "type": "access"}
        return jwt.encode(
            payload, configs.SECRET_KEY.get_secret_value(), algorithm=configs.ALGORITHM
        )

    @override
    def decode_token(self, token: str) -> dict[str, object]:
        configs = get_configs()
        try:
            payload: dict[str, object] = jwt.decode(
                token,
                configs.SECRET_KEY.get_secret_value(),
                algorithms=[configs.ALGORITHM],
            )
            return payload
        except ExpiredSignatureError as exc:
            raise TokenExpiredError() from exc
        except JWTError as exc:
            raise InvalidTokenError() from exc
