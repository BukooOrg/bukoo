from app.domain.entities import AuthorEntity
from app.infrastructure.db.models import AuthorModel

from .base_mapper import BaseMapper


class AuthorMapper(BaseMapper[AuthorModel, AuthorEntity]):
    @staticmethod
    def to_entity(model: AuthorModel) -> AuthorEntity:
        return AuthorEntity(
            _id=model.id,
            _name=model.name,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: AuthorEntity) -> AuthorModel:
        model = AuthorModel(
            name=entity.name,
        )
        model.id = entity.id
        return model
