from app.domain.entities import NotificationEntity
from app.infrastructure.db.models import NotificationModel

from .base_mapper import BaseMapper


class NotificationMapper(BaseMapper[NotificationModel, NotificationEntity]):
    @staticmethod
    def to_entity(model: NotificationModel) -> NotificationEntity:
        return NotificationEntity(
            _id=model.id,
            _user_id=model.user_id,
            _type=model.type,
            _subject=model.subject,
            _body=model.body,
            _status=model.status,
            _sent_at=model.sent_at,
            _read_at=model.read_at,
            _created_at=model.created_at,
            # NotificationModel has no updated_at by design.
        )

    @staticmethod
    def to_model(entity: NotificationEntity) -> NotificationModel:
        model = NotificationModel(
            type=entity.type,
            subject=entity.subject,
            body=entity.body,
            status=entity.status,
        )
        model.id = entity.id
        model.user_id = entity.user_id
        model.sent_at = entity.sent_at
        model.read_at = entity.read_at
        return model
