from app.domain.entities import CartEntity
from app.infrastructure.db.models import CartModel

from .base_mapper import BaseMapper
from .cart_item_mapper import CartItemMapper


class CartMapper(BaseMapper[CartModel, CartEntity]):
    @staticmethod
    def to_entity(model: CartModel) -> CartEntity:
        return CartEntity(
            _id=model.id,
            _user_id=model.user_id,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _cart_items=[CartItemMapper.to_entity(i) for i in model.cart_items],
        )

    @staticmethod
    def to_model(entity: CartEntity) -> CartModel:
        model = CartModel()
        # PK and FK columns are init=False in the ORM — assign directly.
        model.id = entity.id
        model.user_id = entity.user_id
        return model
