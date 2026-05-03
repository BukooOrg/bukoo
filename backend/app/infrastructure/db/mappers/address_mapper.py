from app.domain.entities import AddressEntity
from app.infrastructure.db.models import AddressModel

from .base_mapper import BaseMapper


class AddressMapper(BaseMapper[AddressModel, AddressEntity]):
    @staticmethod
    def to_entity(model: AddressModel) -> AddressEntity:
        return AddressEntity(
            _id=model.id,
            _user_id=model.user_id,
            _recipient_name=model.recipient_name,
            _phone=model.phone,
            _address_line1=model.address_line1,
            _address_line2=model.address_line2,
            _city=model.city,
            _state=model.state,
            _postcode=model.postcode,
            _country=model.country,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
        )

    @staticmethod
    def to_model(entity: AddressEntity) -> AddressModel:
        model = AddressModel(
            recipient_name=entity.recipient_name,
            phone=entity.phone,
            address_line1=entity.address_line1,
            address_line2=entity.address_line2,
            city=entity.city,
            state=entity.state,
            postcode=entity.postcode,
            country=entity.country,
        )
        model.id = entity.id
        model.user_id = entity.user_id
        return model
