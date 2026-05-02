from app.domain.entities import WishlistEntity
from app.infrastructure.db.models import WishlistModel

from .base_mapper import BaseMapper
from .wishlist_item_mapper import WishlistItemMapper


class WishlistMapper(BaseMapper[WishlistModel, WishlistEntity]):
    @staticmethod
    def to_entity(model: WishlistModel) -> WishlistEntity:
        return WishlistEntity(
            _id=model.id,
            _user_id=model.user_id,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _wishlist_items=[
                WishlistItemMapper.to_entity(i) for i in model.wishlist_items
            ],
        )

    @staticmethod
    def to_model(entity: WishlistEntity) -> WishlistModel:
        model = WishlistModel()
        model.id = entity.id
        model.user_id = entity.user_id
        return model
