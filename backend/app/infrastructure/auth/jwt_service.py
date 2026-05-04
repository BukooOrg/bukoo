from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import override
from uuid import uuid4

from jose import JWTError, jwt
from jose.exceptions import ExpiredSignatureError

from app.application.interfaces.cache_service import ICacheService
from app.application.interfaces.token_service import ITokenService
from app.core.config import get_configs
from app.domain.exceptions import InvalidTokenError, TokenExpiredError


class JWTService(ITokenService):
    def __init__(self, cache_svc: ICacheService) -> None:
        self._cache_svc = cache_svc

    @override
    def create_access_token(self, subject: str) -> str:
        configs = get_configs()
        expire = datetime.now(UTC) + timedelta(
            minutes=configs.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        payload = {
            "sub": subject,
            "exp": expire,
            "type": "access",
            "jti": str(uuid4()),
        }

        return jwt.encode(
            payload, configs.SECRET_KEY.get_secret_value(), algorithm=configs.ALGORITHM
        )

    @override
    def decode_token(
        self,
        token: str,
        *,
        verify_exp: bool = True,
    ) -> dict[str, object]:
        configs = get_configs()

        try:
            payload: dict[str, object] = jwt.decode(
                token,
                configs.SECRET_KEY.get_secret_value(),
                algorithms=[configs.ALGORITHM],
                options={"verify_exp": verify_exp},
            )
            return payload

        except ExpiredSignatureError as exc:
            # Only raise if we explicitly care about expiration
            if verify_exp:
                raise TokenExpiredError() from exc

            # If verify_exp=False, we should NOT reach here in most libs,
            # but keep this as a defensive fallback.
            payload = jwt.decode(
                token,
                configs.SECRET_KEY.get_secret_value(),
                algorithms=[configs.ALGORITHM],
                options={"verify_exp": False},
            )
            return payload

        except JWTError as exc:
            raise InvalidTokenError() from exc

    @override
    async def revoke_token(self, payload: dict[str, object]) -> None:
        jti = str(payload.get("jti", ""))
        exp = payload.get("exp")

        # ignore invalid or expired token
        # don't need to store for validation later
        if not jti or exp is None:
            return

        ttl = int(float(str(exp))) - int(datetime.now(UTC).timestamp())
        if ttl > 0:
            await self._cache_svc.set(f"blocklist:{jti}", "1", ttl_seconds=ttl)

    @override
    async def is_token_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        return await self._cache_svc.exists(f"blocklist:{jti}")
