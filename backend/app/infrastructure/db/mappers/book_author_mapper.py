from app.core.util import is_loaded
from app.domain.entities import BookAuthorEntity
from app.infrastructure.db.models import BookAuthorModel

from .author_mapper import AuthorMapper
from .base_mapper import BaseMapper


class BookAuthorMapper(BaseMapper[BookAuthorModel, BookAuthorEntity]):
    @staticmethod
    def to_entity(model: BookAuthorModel) -> BookAuthorEntity:
        author = None

        if is_loaded(model, "author"):
            author = AuthorMapper.to_entity(model.author) if model.author else None

        return BookAuthorEntity(
            _book_id=model.book_id,
            _author_id=model.author_id,
            _display_order=model.display_order,
            _created_at=model.created_at,
            _updated_at=model.updated_at,
            # selectin-loaded — always present.
            _author=author,
        )

    @staticmethod
    def to_model(entity: BookAuthorEntity) -> BookAuthorModel:
        model = BookAuthorModel(
            display_order=entity.display_order,
        )
        model.book_id = entity.book_id
        model.author_id = entity.author_id
        return model
