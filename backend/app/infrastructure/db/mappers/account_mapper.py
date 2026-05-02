from app.domain.entities import AccountEntity
from app.infrastructure.db.models import AccountModel

from .base_mapper import BaseMapper


class AccountMapper(BaseMapper[AccountModel, AccountEntity]):
    @staticmethod
    def to_entity(model: AccountModel) -> AccountEntity:
        return AccountEntity(
            _id=model.id,
            _user_id=model.user_id,
            _provider=model.provider,
            _open_id=model.open_id,
            _encrypted_token=model.encrypted_token,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: AccountEntity) -> AccountModel:
        model = AccountModel(
            provider=entity.provider,
            open_id=entity.open_id,
            encrypted_token=entity.encrypted_token,
        )

        model.id = entity.id
        model.user_id = entity.user_id
        return model
