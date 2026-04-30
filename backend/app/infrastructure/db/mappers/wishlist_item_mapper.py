from app.domain.entities import WishlistItemEntity
from app.infrastructure.db.models import WishlistItemModel

from .base_mapper import BaseMapper
from .book_mapper import BookMapper


class WishlistItemMapper(BaseMapper[WishlistItemModel, WishlistItemEntity]):
    @staticmethod
    def to_entity(model: WishlistItemModel) -> WishlistItemEntity:
        return WishlistItemEntity(
            _id=model.id,
            _wishlist_id=model.wishlist_id,
            _book_id=model.book_id,
            _added_at=model.added_at,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _book=BookMapper.to_entity(model.book),
        )

    @staticmethod
    def to_model(entity: WishlistItemEntity) -> WishlistItemModel:
        model = WishlistItemModel()
        model.id = entity.id
        model.wishlist_id = entity.wishlist_id
        model.book_id = entity.book_id
        return model
