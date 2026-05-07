from __future__ import annotations

import urllib.parse
from datetime import UTC, date, datetime
from typing import override

import httpx
import structlog
from uuid_extension import uuid7

from app.application.dtos.auth_dto import AuthResult, OAuthUserInfo
from app.application.interfaces.auth_provider import IAuthProvider
from app.application.interfaces.oauth_provider import IOAuthProvider
from app.application.interfaces.storage_service import IStorageService
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.core.util import download_content
from app.domain.entities import AccountEntity, UserEntity
from app.domain.exceptions.auth import FacebookOAuthError, UserSuspendedError
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository

logger = structlog.get_logger(__name__)

_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
_USERINFO_URL = "https://graph.facebook.com/me"
_USERINFO_FIELDS = "id,name,email,picture.type(large),birthday"


class FacebookAuthProvider(IAuthProvider, IOAuthProvider):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
        storage_svc: IStorageService,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo
        self._storage_svc = storage_svc
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    @override
    def get_authorization_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "scope": "email,public_profile",
            "state": state,
            "response_type": "code",
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @override
    async def get_access_token(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    _TOKEN_URL,
                    params={
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "redirect_uri": self._redirect_uri,
                        "code": code,
                    },
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FacebookOAuthError() from exc

            data: dict[str, str] = response.json()
            access_token = data.get("access_token")
            if not access_token:
                raise FacebookOAuthError()
            return access_token

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    _USERINFO_URL,
                    params={"fields": _USERINFO_FIELDS, "access_token": token},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise FacebookOAuthError() from exc

            info: dict[str, object] = response.json()
            email = info.get("email")
            if not email or not isinstance(email, str):
                raise FacebookOAuthError()

            picture_url: str | None = None
            picture = info.get("picture")
            if isinstance(picture, dict):
                data = picture.get("data")
                if isinstance(data, dict):
                    url = data.get("url")
                    if isinstance(url, str):
                        picture_url = url

            dob: date | None = None
            birthday = info.get("birthday")

            if isinstance(birthday, str):
                parts = birthday.split("/")

                try:
                    if len(parts) == 3:
                        month, day, year = map(int, parts)
                        dob = date(year=year, month=month, day=day)
                except ValueError as exc:
                    logger.info("failed to parse dob", exc=exc)
            else:
                logger.info("User have not dob")

            return OAuthUserInfo(
                id=str(info["id"]),
                email=email,
                name=str(info.get("name", "")),
                avatar_url=picture_url,
                date_of_birth=dob,
            )

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        code = payload.get("code", "")
        access_token = await self.get_access_token(code)
        user_info = await self.get_user_info(access_token)

        now = datetime.now(UTC)

        # Branch A: account already linked to this Facebook identity
        existing_account = await self._account_repo.find_by_provider_and_open_id(
            AuthProvider.FACEBOOK, user_info.id
        )
        if existing_account:
            linked_user = await self._user_repo.find_by_id(existing_account.user_id)
            if linked_user:
                if linked_user.status == UserStatus.SUSPENDED:
                    raise UserSuspendedError(linked_user.email)
                existing_account.update_token(access_token)
                await self._account_repo.save(existing_account)
                linked_user.record_login()
                await self._user_repo.save(linked_user)
                return AuthResult(
                    user_id=linked_user.id, email=linked_user.email, is_new_user=False
                )

        # Branch B: find existing user by email or create a new one
        user_by_email = await self._user_repo.find_by_email(user_info.email)
        if user_by_email:
            if user_by_email.status == UserStatus.SUSPENDED:
                raise UserSuspendedError(user_by_email.email)
            if user_by_email.status == UserStatus.PENDING:
                user_by_email.activate()
            user: UserEntity = user_by_email
            is_new_user = False
        else:
            user_id = str(uuid7())
            avatar_key = None
            if user_info.avatar_url:
                avatar_data = await download_content(user_info.avatar_url)
                if avatar_data:
                    avatar_bytes, content_type = avatar_data
                    avatar_key = f"pub/avatars/{user_id}"
                    try:
                        await self._storage_svc.upload(
                            avatar_key, avatar_bytes, content_type
                        )
                    except Exception as exc:
                        logger.debug("Failed to upload cover image to object storage")
                        logger.debug(exc)

                        avatar_key = None
            user = UserEntity(
                _id=user_id,
                _email=user_info.email,
                _full_name=user_info.name,
                _date_of_birth=user_info.date_of_birth,
                _role=UserRole.USER,
                _status=UserStatus.ACTIVE,
                _hashed_password=None,
                _avatar_url=avatar_key,
                _last_login_at=None,
                _created_at=now,
                _updated_at=now,
                _deleted_at=None,
            )
            await self._user_repo.save(user)
            is_new_user = True

        new_account = AccountEntity(
            _id=str(uuid7()),
            _user_id=user.id,
            _provider=AuthProvider.FACEBOOK,
            _open_id=user_info.id,
            _encrypted_token=access_token,
            _created_at=now,
            _updated_at=now,
        )
        await self._account_repo.save(new_account)
        user.record_login()
        await self._user_repo.save(user)

        return AuthResult(user_id=user.id, email=user.email, is_new_user=is_new_user)
