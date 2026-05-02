from app.domain.entities import PublisherEntity
from app.infrastructure.db.models import PublisherModel

from .base_mapper import BaseMapper


class PublisherMapper(BaseMapper[PublisherModel, PublisherEntity]):
    @staticmethod
    def to_entity(model: PublisherModel) -> PublisherEntity:
        return PublisherEntity(
            _id=model.id,
            _name=model.name,
            _website=model.website,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: PublisherEntity) -> PublisherModel:
        model = PublisherModel(
            name=entity.name,
            website=entity.website,
        )
        model.id = entity.id
        return model
