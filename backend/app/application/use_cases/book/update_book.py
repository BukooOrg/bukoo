from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.book_dto import UpdateBookCommand, UpdateBookResult
from app.domain.entities.book_author_entity import BookAuthorEntity
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.publisher_entity import PublisherEntity
from app.domain.exceptions import (
    AuthorNotFoundError,
    BookAlreadyExistsError,
    BookNotFoundError,
    CategoryNotFoundError,
    PublisherNotFoundError,
)
from app.domain.repositories import (
    BookStatusFilter,
    IAuthorRepository,
    IBookRepository,
    ICategoryRepository,
    IPublisherRepository,
)

from .base import BaseBookUseCase


class UpdateBookUseCase(BaseBookUseCase):
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
    async def execute(self, cmd: UpdateBookCommand) -> UpdateBookResult:
        book = await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter("all"))
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        isbn = book.isbn
        if cmd.isbn is not None:
            if cmd.isbn == "null":
                isbn = None
            else:
                isbn_book = await self._book_repo.find_by_isbn(cmd.isbn)
                if isbn_book is not None and isbn_book.id != book.id:
                    raise BookAlreadyExistsError(cmd.isbn)
                isbn = cmd.isbn

        description = book.description
        if cmd.description is not None:
            description = None if cmd.description == "null" else cmd.description

        page_count = book.page_count
        if cmd.page_count is not None:
            page_count = None if cmd.page_count == "null" else cmd.page_count

        published_date = book.published_date
        if cmd.published_date is not None:
            published_date = (
                None if cmd.published_date == "null" else cmd.published_date
            )

        publisher: PublisherEntity | None = book.publisher
        if cmd.publisher_id is not None:
            if cmd.publisher_id == "null":
                publisher = None
            else:
                resolved_publisher = await self._publisher_repo.find_by_id(
                    cmd.publisher_id
                )
                if resolved_publisher is None:
                    raise PublisherNotFoundError(cmd.publisher_id)
                publisher = resolved_publisher

        category: CategoryEntity | None = book.category
        if cmd.category_id is not None:
            if cmd.category_id == "null":
                category = None
            else:
                resolved_category = await self._category_repo.find_by_id(
                    cmd.category_id
                )
                if resolved_category is None:
                    raise CategoryNotFoundError(cmd.category_id)
                category = resolved_category

        authors: list[BookAuthorEntity] = list(book.authors)
        if cmd.authors is not None:
            if cmd.authors == "null":
                authors = []
            else:
                now = datetime.now(UTC)
                authors = []
                for item in cmd.authors:
                    author_entity = await self._author_repo.find_by_id(item.author_id)
                    if author_entity is None:
                        raise AuthorNotFoundError(item.author_id)
                    book_author = BookAuthorEntity(
                        _book_id=book.id,
                        _author_id=item.author_id,
                        _display_order=item.display_order,
                        _created_at=now,
                        _updated_at=now,
                    )
                    book_author.set_author(author_entity)
                    authors.append(book_author)

        book.update(
            title=cmd.title or book.title,
            price=cmd.price or book.price,
            stock_quantity=cmd.stock_quantity or book.stock_quantity,
            language=cmd.language or book.language,
            isbn=isbn,
            description=description,
            page_count=page_count,
            published_date=published_date,
            publisher=publisher,
            category=category,
            authors=authors,
        )
        await self._book_repo.save(book, False)
        await self._db_session.commit()

        return self._to_result(book, UpdateBookResult)
