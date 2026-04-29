"""
GoogleProvider — Strategy pattern: Google OAuth2 authentication.

Flow:
  1. Exchange auth code for access token.
  2. Fetch user info from Google.
  3. Look up the OAuth account record by (provider, open_id).
  4. If found → return the linked user.
  5. If not found → check if a user with the same email already exists.
       - Exists → link the Google account to the existing user.
       - Does not exist → create a new PENDING user + link account.
         (User stays PENDING; email verification activates them.)
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import override

import httpx
from uuid_extension import uuid7

from app.application.dtos.auth_dto import AuthResult
from app.application.interfaces.auth_provider import IAuthStrategy
from app.core.config import get_configs
from app.core.constants import AuthProvider, UserRole, UserStatus
from app.domain.entities.user import AccountEntity, UserEntity
from app.domain.repositories.account_repository import IAccountRepository
from app.domain.repositories.user_repository import IUserRepository

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleProvider(IAuthStrategy):
    def __init__(
        self,
        user_repo: IUserRepository,
        account_repo: IAccountRepository,
    ) -> None:
        self._user_repo = user_repo
        self._account_repo = account_repo

    @override
    async def authenticate(self, payload: dict[str, str]) -> AuthResult:
        configs = get_configs()
        code = payload.get("code", "")
        redirect_uri = payload.get("redirect_uri", "") or configs.GOOGLE_REDIRECT_URI

        # 1. Exchange code for token
        async with httpx.AsyncClient() as client:
            token_res = await client.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "client_id": configs.GOOGLE_CLIENT_ID,
                    "client_secret": configs.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            token_res.raise_for_status()
            token_data: dict[str, str] = token_res.json()
            access_token = token_data["access_token"]

            # 2. Fetch user info
            user_res = await client.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            user_res.raise_for_status()
            info: dict[str, str] = user_res.json()

        email: str = info["email"]
        full_name: str = info.get("name", email)
        open_id: str = info["id"]
        avatar_url: str | None = info.get("picture")
        provider = AuthProvider.GOOGLE.value

        #  3. Look up existing OAuth account link
        existing_account = await self._account_repo.find_by_provider_and_open_id(
            provider, open_id
        )
        if existing_account:
            user = await self._user_repo.find_by_id(existing_account.user_id)
            if user:
                user.record_login()
                await self._user_repo.save(user)
                return AuthResult(user_id=user.id, email=user.email, is_new_user=False)

        # 4. No OAuth link — look up by email
        now = datetime.now(UTC)
        existing_user = await self._user_repo.find_by_email(email)

        if existing_user:
            user = existing_user
        else:
            # 5. Brand-new user — create with PENDING status
            user = UserEntity(
                id=str(uuid7()),
                email=email,
                full_name=full_name,
                role=UserRole.USER,
                status=UserStatus.PENDING,
                hashed_password=None,  # OAuth-only account
                avatar_url=avatar_url,
                last_login_at=now,
                created_at=now,
                updated_at=now,
                deleted_at=None,
            )
            await self._user_repo.save(user)

        #  6. Link the OAuth account
        account = AccountEntity(
            id=str(uuid7()),
            user_id=user.id,
            provider=provider,
            open_id=open_id,
            encrypted_token=access_token,  # encrypt before storing in production
            created_at=now,
            updated_at=now,
        )
        await self._account_repo.save(account)

        user.record_login()
        await self._user_repo.save(user)

        return AuthResult(
            user_id=user.id,
            email=user.email,
            is_new_user=existing_user is None,
        )
