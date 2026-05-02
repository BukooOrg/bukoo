from app.domain.entities import ReviewEntity
from app.infrastructure.db.models import ReviewModel

from .base_mapper import BaseMapper


class ReviewMapper(BaseMapper[ReviewModel, ReviewEntity]):
    @staticmethod
    def to_entity(model: ReviewModel) -> ReviewEntity:
        return ReviewEntity(
            _id=model.id,
            _user_id=model.user_id,
            _book_id=model.book_id,
            _order_item_id=model.order_item_id,
            _rating=model.rating,
            _comment=model.comment,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
        )

    @staticmethod
    def to_model(entity: ReviewEntity) -> ReviewModel:
        model = ReviewModel(
            rating=entity.rating,
            comment=entity.comment,
        )
        model.id = entity.id
        model.user_id = entity.user_id
        model.book_id = entity.book_id
        model.order_item_id = entity.order_item_id
        model.deleted_at = entity.deleted_at
        return model
