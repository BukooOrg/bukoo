from __future__ import annotations

from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import (
    BaseBookResult,
    BookAuthorItemResult,
    BookCategoryResult,
    BookPublisherResult,
)
from app.domain.entities import BookEntity
from app.domain.repositories import IBookRepository

from ..base import BaseUseCase

T = TypeVar("T", bound=BaseBookResult)


class BaseBookUseCase(BaseUseCase):
    def __init__(self, db_session: AsyncSession, book_repo: IBookRepository) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo

    @staticmethod
    def _to_result(book: BookEntity, cls: type[T]) -> T:
        publisher = (
            BookPublisherResult(id=book.publisher.id, name=book.publisher.name)
            if book.publisher
            else None
        )
        category = (
            BookCategoryResult(id=book.category.id, name=book.category.name)
            if book.category
            else None
        )
        authors = [
            BookAuthorItemResult(
                id=ba.author_id,
                name=ba.author.name if ba.author else "",
                display_order=ba.display_order,
            )
            for ba in book.authors
        ]
        return cls(
            id=book.id,
            title=book.title,
            price=book.price,
            language=book.language,
            stock_quantity=book.stock_quantity,
            cover_url=book.cover_url,
            isbn=book.isbn,
            description=book.description,
            page_count=book.page_count,
            published_date=book.published_date,
            is_active=book.is_active,
            publisher=publisher,
            category=category,
            authors=authors,
            created_at=book.created_at,
            updated_at=book.updated_at,
        )
