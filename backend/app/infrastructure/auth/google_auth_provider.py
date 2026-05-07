from __future__ import annotations

import urllib.parse
from datetime import UTC, date, datetime
from typing import Any, override

import httpx
import structlog
from uuid_extension import uuid7

from app.application.dtos.auth_dto import AuthResult, OAuthUserInfo
from app.application.interfaces import IAuthProvider, IOAuthProvider
from app.application.interfaces.storage_service import IStorageService
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.core.util import download_content
from app.domain.entities import AccountEntity, UserEntity
from app.domain.exceptions.auth import GoogleOAuthError, UserSuspendedError
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository

logger = structlog.get_logger(__name__)

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"
_PEOPLE_API_URL = "https://people.googleapis.com/v1/people/me"


class GoogleAuthProvider(IAuthProvider, IOAuthProvider):
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
            "response_type": "code",
            "redirect_uri": self._redirect_uri,
            "scope": "openid email profile https://www.googleapis.com/auth/user.birthday.read",
            "state": state,
        }
        return f"{_AUTH_URL}?{urllib.parse.urlencode(params)}"

    @override
    async def get_access_token(self, code: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    _TOKEN_URL,
                    data={
                        "code": code,
                        "client_id": self._client_id,
                        "client_secret": self._client_secret,
                        "redirect_uri": self._redirect_uri,
                        "grant_type": "authorization_code",
                    },
                    headers={"Accept": "application/json"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise GoogleOAuthError() from exc

            data: dict[str, str] = response.json()
            access_token = data.get("access_token")
            if not access_token:
                raise GoogleOAuthError()
            return access_token

    @override
    async def get_user_info(self, token: str) -> OAuthUserInfo:
        async with httpx.AsyncClient() as client:
            # get user info
            try:
                response = await client.get(
                    _USERINFO_URL,
                    headers={"Authorization": f"Bearer {token}"},
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                raise GoogleOAuthError() from exc

            info: dict[str, Any] = response.json()

            # get DOB from People API
            dob: date | None = None
            try:
                people_resp = await client.get(
                    _PEOPLE_API_URL,
                    params={"personFields": "birthdays"},
                    headers={"Authorization": f"Bearer {token}"},
                )
                people_resp.raise_for_status()
                people_data = people_resp.json()

                birthdays = people_data.get("birthdays", [])
                if birthdays:
                    birth_date = birthdays[0].get("date", {})
                    year = birth_date.get("year")
                    month = birth_date.get("month")
                    day = birth_date.get("day")

                    if year and month and day:
                        dob = date(year=year, month=month, day=day)

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "google_dob_not_available",
                    status_code=exc.response.status_code,
                    response=exc.response.text,
                )

            return OAuthUserInfo(
                id=info["sub"],
                email=info["email"],
                name=info.get("name", ""),
                avatar_url=info.get("picture"),
                date_of_birth=dob,
            )

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        code = payload.get("code", "")
        access_token = await self.get_access_token(code)
        user_info = await self.get_user_info(access_token)

        now = datetime.now(UTC)

        # Branch A: account already linked to this Google identity
        existing_account = await self._account_repo.find_by_provider_and_open_id(
            AuthProvider.GOOGLE, user_info.id
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
                        logger.error("Failed to upload cover image to object storage")
                        logger.error(exc)

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
            _provider=AuthProvider.GOOGLE,
            _open_id=user_info.id,
            _encrypted_token=access_token,
            _created_at=now,
            _updated_at=now,
        )
        await self._account_repo.save(new_account)
        user.record_login()
        await self._user_repo.save(user)

        return AuthResult(user_id=user.id, email=user.email, is_new_user=is_new_user)
