from app.domain.entities import OrderItemEntity
from app.infrastructure.db.models import OrderItemModel

from .base_mapper import BaseMapper
from .book_mapper import BookMapper


class OrderItemMapper(BaseMapper[OrderItemModel, OrderItemEntity]):
    @staticmethod
    def to_entity(model: OrderItemModel) -> OrderItemEntity:
        return OrderItemEntity(
            _id=model.id,
            _order_id=model.order_id,
            _book_id=model.book_id,
            _book_title=model.book_title,
            _unit_price=model.unit_price,
            _quantity=model.quantity,
            _line_total=model.line_total,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — may be None if the book was hard-deleted.
            _book=(
                BookMapper.to_entity(model.book) if model.book is not None else None
            ),
        )

    @staticmethod
    def to_model(entity: OrderItemEntity) -> OrderItemModel:
        model = OrderItemModel(
            book_title=entity.book_title,
            unit_price=entity.unit_price,
            quantity=entity.quantity,
            line_total=entity.line_total,
        )
        model.id = entity.id
        model.order_id = entity.order_id
        model.book_id = entity.book_id
        return model
