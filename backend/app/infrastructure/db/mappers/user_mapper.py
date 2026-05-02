from app.domain.entities import UserEntity
from app.infrastructure.db.models import UserModel

from .account_mapper import AccountMapper
from .address_mapper import AddressMapper
from .base_mapper import BaseMapper


class UserMapper(BaseMapper[UserModel, UserEntity]):
    @staticmethod
    def to_entity(model: UserModel) -> UserEntity:
        return UserEntity(
            _id=model.id,
            _email=model.email,
            _full_name=model.full_name,
            _date_of_birth=model.date_of_birth,
            _role=model.role,
            _status=model.status,
            _hashed_password=model.hashed_password,
            _avatar_url=model.avatar_url,
            _last_login_at=model.last_login_at,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
            # selectin-loaded — always present (may be empty list).
            _accounts=[AccountMapper.to_entity(a) for a in model.accounts],
            # selectin-loaded — None if the user has no saved address yet.
            _address=(
                AddressMapper.to_entity(model.address)
                if model.address is not None
                else None
            ),
        )

    @staticmethod
    def to_model(entity: UserEntity) -> UserModel:
        model = UserModel(
            email=entity.email,
            full_name=entity.full_name,
            date_of_birth=entity.date_of_birth,
            hashed_password=entity.hashed_password,
            avatar_url=entity.avatar_url,
            role=entity.role,
            status=entity.status,
            last_login_at=entity.last_login_at,
        )
        model.id = entity.id
        model.deleted_at = entity.deleted_at
        return model
