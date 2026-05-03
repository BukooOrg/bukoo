from app.domain.entities import OrderEntity
from app.infrastructure.db.models import OrderModel

from .base_mapper import BaseMapper
from .order_item_mapper import OrderItemMapper
from .payment_mapper import PaymentMapper


class OrderMapper(BaseMapper[OrderModel, OrderEntity]):
    @staticmethod
    def to_entity(model: OrderModel) -> OrderEntity:
        return OrderEntity(
            _id=model.id,
            _user_id=model.user_id,
            _address_snapshot=model.address_snapshot,
            _subtotal=model.subtotal,
            _shipping_cost=model.shipping_cost,
            _total=model.total,
            _status=model.status,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _order_items=[OrderItemMapper.to_entity(i) for i in model.order_items],
            _payments=[PaymentMapper.to_entity(i) for i in model.payments],
        )

    @staticmethod
    def to_model(entity: OrderEntity) -> OrderModel:
        model = OrderModel(
            address_snapshot=entity.address_snapshot,
            subtotal=entity.subtotal,
            shipping_cost=entity.shipping_cost,
            total=entity.total,
            status=entity.status,
        )
        model.id = entity.id
        model.user_id = entity.user_id
        return model
