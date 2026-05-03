from __future__ import annotations

from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.infrastructure.db.models.verification_token_model import VerificationTokenModel

from .base_mapper import BaseMapper


class VerificationTokenMapper(
    BaseMapper[VerificationTokenModel, VerificationTokenEntity]
):
    @staticmethod
    def to_entity(model: VerificationTokenModel) -> VerificationTokenEntity:
        return VerificationTokenEntity(
            _id=model.id,
            _user_id=model.user_id,
            _token_hash=model.token_hash,
            _type=model.type,
            _expires_at=model.expires_at,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _used_at=model.used_at,
        )

    @staticmethod
    def to_model(entity: VerificationTokenEntity) -> VerificationTokenModel:
        model = VerificationTokenModel(
            user_id=entity.user_id,
            token_hash=entity.token_hash,
            type=entity.type,
            expires_at=entity.expires_at,
        )
        model.id = entity.id
        model.used_at = entity.used_at
        return model
