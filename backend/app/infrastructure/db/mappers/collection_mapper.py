from app.domain.entities import CollectionEntity
from app.infrastructure.db.models import CollectionModel

from .base_mapper import BaseMapper
from .category_mapper import CategoryMapper


class CollectionMapper(BaseMapper[CollectionModel, CollectionEntity]):
    @staticmethod
    def to_entity(model: CollectionModel) -> CollectionEntity:
        return CollectionEntity(
            _id=model.id,
            _name=model.name,
            _url_slug=model.url_slug,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
            # selectin-loaded — always present.
            _categories=[CategoryMapper.to_entity(c) for c in model.categories],
        )

    @staticmethod
    def to_model(entity: CollectionEntity) -> CollectionModel:
        model = CollectionModel(
            name=entity.name,
            url_slug=entity.url_slug,
        )
        model.id = entity.id
        model.deleted_at = entity.deleted_at
        return model
