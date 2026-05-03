from app.domain.entities import CartItemEntity
from app.infrastructure.db.models import CartItemModel

from .base_mapper import BaseMapper
from .book_mapper import BookMapper


class CartItemMapper(BaseMapper[CartItemModel, CartItemEntity]):
    @staticmethod
    def to_entity(model: CartItemModel) -> CartItemEntity:
        return CartItemEntity(
            _id=model.id,
            _cart_id=model.cart_id,
            _book_id=model.book_id,
            _quantity=model.quantity,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _book=BookMapper.to_entity(model.book),
        )

    @staticmethod
    def to_model(entity: CartItemEntity) -> CartItemModel:
        model = CartItemModel(
            quantity=entity.quantity,
        )
        model.id = entity.id
        model.cart_id = entity.cart_id
        model.book_id = entity.book_id
        return model
