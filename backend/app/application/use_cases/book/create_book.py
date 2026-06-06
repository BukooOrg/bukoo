from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.book_dto import CreateBookCommand, CreateBookResult
from app.domain.entities.book_author_entity import BookAuthorEntity
from app.domain.entities.book_entity import BookEntity
from app.domain.exceptions import (
    AuthorNotFoundError,
    BookAlreadyExistsError,
    CategoryNotFoundError,
    PublisherNotFoundError,
)
from app.domain.repositories import (
    IAuthorRepository,
    IBookRepository,
    ICategoryRepository,
    IPublisherRepository,
)

from .base import BaseBookUseCase


class CreateBookUseCase(BaseBookUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        publisher_repo: IPublisherRepository,
        category_repo: ICategoryRepository,
        author_repo: IAuthorRepository,
    ) -> None:
        super().__init__(db_session=db_session, book_repo=book_repo)
        self._publisher_repo = publisher_repo
        self._category_repo = category_repo
        self._author_repo = author_repo

    @override
    async def execute(self, cmd: CreateBookCommand) -> CreateBookResult:
        if cmd.isbn is not None:
            existing = await self._book_repo.find_by_isbn(cmd.isbn)
            if existing is not None:
                raise BookAlreadyExistsError(cmd.isbn)

        publisher = None
        if cmd.publisher_id is not None:
            publisher = await self._publisher_repo.find_by_id(cmd.publisher_id)
            if publisher is None:
                raise PublisherNotFoundError(cmd.publisher_id)

        category = None
        if cmd.category_id is not None:
            category = await self._category_repo.find_by_id(cmd.category_id)
            if category is None:
                raise CategoryNotFoundError(cmd.category_id)

        author_entities = {}
        for item in cmd.authors:
            author = await self._author_repo.find_by_id(item.author_id)
            if author is None:
                raise AuthorNotFoundError(item.author_id)
            author_entities[item.author_id] = author

        now = datetime.now(UTC)
        book = BookEntity(
            _id=str(uuid7()),
            _title=cmd.title,
            _price=cmd.price,
            _stock_quantity=cmd.stock_quantity,
            _language=cmd.language,
            _publisher_id=cmd.publisher_id,
            _category_id=cmd.category_id,
            _isbn=cmd.isbn,
            _description=cmd.description,
            _cover_url=None,
            _page_count=cmd.page_count,
            _published_date=cmd.published_date,
            _deactivated_at=None,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )

        if publisher is not None:
            book.set_publisher(publisher)
        if category is not None:
            book.set_category(category)

        for item in cmd.authors:
            book_author = BookAuthorEntity(
                _book_id=book.id,
                _author_id=item.author_id,
                _display_order=item.display_order,
                _created_at=now,
                _updated_at=now,
            )
            book_author.set_author(author_entities[item.author_id])
            book.set_author(book_author)

        await self._book_repo.save(book, False)
        try:
            await self._db_session.commit()
        except IntegrityError:
            await self._db_session.rollback()
            if cmd.isbn is not None:
                raise BookAlreadyExistsError(cmd.isbn) from None
            raise

        return self._to_result(book, CreateBookResult)
