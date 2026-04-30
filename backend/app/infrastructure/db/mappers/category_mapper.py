from app.domain.entities import CategoryEntity
from app.infrastructure.db.models import CategoryModel

from .base_mapper import BaseMapper


class CategoryMapper(BaseMapper[CategoryModel, CategoryEntity]):
    @staticmethod
    def to_entity(model: CategoryModel) -> CategoryEntity:
        return CategoryEntity(
            _id=model.id,
            _collection_id=model.collection_id,
            _name=model.name,
            _url_slug=model.url_slug,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: CategoryEntity) -> CategoryModel:
        model = CategoryModel(
            name=entity.name,
            url_slug=entity.url_slug,
        )
        model.id = entity.id
        model.collection_id = entity.collection_id
        model.deleted_at = entity.deleted_at
        return model
