from app.domain.entities import BookEntity
from app.infrastructure.db.models import BookModel

from .base_mapper import BaseMapper
from .book_author_mapper import BookAuthorMapper
from .category_mapper import CategoryMapper
from .publisher_mapper import PublisherMapper


class BookMapper(BaseMapper[BookModel, BookEntity]):
    @staticmethod
    def to_entity(model: BookModel) -> BookEntity:
        return BookEntity(
            _id=model.id,
            _title=model.title,
            _price=model.price,
            _stock_quantity=model.stock_quantity,
            _language=model.language,
            _publisher_id=model.publisher_id,
            _category_id=model.category_id,
            _isbn=model.isbn,
            _description=model.description,
            _cover_url=model.cover_url,
            _page_count=model.page_count,
            _published_date=model.published_date,
            _deactivated_at=model.deactivated_at,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            _deleted_at=model.deleted_at,
            # selectin-loaded — resolve to nested entities when present.
            _publisher=(
                PublisherMapper.to_entity(model.publisher)
                if model.publisher is not None
                else None
            ),
            _category=(
                CategoryMapper.to_entity(model.category)
                if model.category is not None
                else None
            ),
            # selectin-loaded and ordered by display_order on the ORM side.
            _authors=[BookAuthorMapper.to_entity(a) for a in model.author_associations],
        )

    @staticmethod
    def to_model(entity: BookEntity) -> BookModel:
        model = BookModel(
            title=entity.title,
            price=entity.price,
            isbn=entity.isbn,
            description=entity.description,
            cover_url=entity.cover_url,
            stock_quantity=entity.stock_quantity,
            page_count=entity.page_count,
            language=entity.language,
            published_date=entity.published_date,
        )
        model.id = entity.id
        model.publisher_id = entity.publisher_id
        model.category_id = entity.category_id
        model.deactivated_at = entity.deactivated_at
        model.deleted_at = entity.deleted_at
        return model
