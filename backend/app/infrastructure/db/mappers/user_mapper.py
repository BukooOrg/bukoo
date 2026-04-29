"""
UserMapper and AccountMapper.
Convert between ORM models (infrastructure) and domain entities (domain).
Neither side imports from the other's layer — the mapper sits in infrastructure
and knows about both, which is acceptable (it IS infrastructure).
"""

from __future__ import annotations

from app.core.constants import UserRole, UserStatus
from app.domain.entities.user import AccountEntity, UserEntity
from app.infrastructure.db.models.user_model import AccountModel, UserModel

from .util import _utc


class UserMapper:
    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        return UserEntity(
            id=model.id,
            email=model.email,
            full_name=model.full_name,
            role=UserRole(model.role),
            status=UserStatus(model.status),
            hashed_password=model.hashed_password,
            avatar_url=model.avatar_url,
            last_login_at=_utc(model.last_login_at),  # type: ignore[arg-type]
            created_at=_utc(model.created_at),  # type: ignore[arg-type]
            updated_at=_utc(model.updated_at),  # type: ignore[arg-type]
            deleted_at=_utc(model.deleted_at),  # type: ignore[arg-type]
        )

    @staticmethod
    def to_model(entity: UserEntity) -> UserModel:
        return UserModel(
            email=entity.email,
            full_name=entity.full_name,
            hashed_password=entity.hashed_password,
            avatar_url=entity.avatar_url,
            role=entity.role.value,
            status=entity.status.value,
            last_login_at=entity.last_login_at,
        )


class AccountMapper:
    @staticmethod
    def to_entity(model: AccountModel) -> AccountEntity:
        return AccountEntity(
            id=model.id,
            user_id=model.user_id,
            provider=model.provider,
            open_id=model.open_id,
            encrypted_token=model.encrypted_token,
            created_at=_utc(model.created_at),  # type: ignore[arg-type]
            updated_at=_utc(model.updated_at),  # type: ignore[arg-type]
        )

    @staticmethod
    def to_model(entity: AccountEntity) -> AccountModel:
        model = AccountModel(
            provider=entity.provider,
            open_id=entity.open_id,
            encrypted_token=entity.encrypted_token,
        )
        model.user_id = entity.user_id

        return model
