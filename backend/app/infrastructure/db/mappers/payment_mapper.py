from app.domain.entities import PaymentEntity
from app.infrastructure.db.models import PaymentModel

from .base_mapper import BaseMapper


class PaymentMapper(BaseMapper[PaymentModel, PaymentEntity]):
    @staticmethod
    def to_entity(model: PaymentModel) -> PaymentEntity:
        return PaymentEntity(
            _id=model.id,
            _order_id=model.order_id,
            _method=model.method,
            _amount=model.amount,
            _status=model.status,
            _simulated_ref=model.simulated_ref,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: PaymentEntity) -> PaymentModel:
        model = PaymentModel(
            method=entity.method,
            amount=entity.amount,
            status=entity.status,
            simulated_ref=entity.simulated_ref,
        )
        model.id = entity.id
        model.order_id = entity.order_id
        return model
