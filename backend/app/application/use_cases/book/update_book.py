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
        if "isbn" in cmd.fields_to_update:
            if cmd.isbn:
                isbn_book = await self._book_repo.find_by_isbn(cmd.isbn)
                if isbn_book and isbn_book.id != book.id:
                    raise BookAlreadyExistsError(cmd.isbn)
            isbn = cmd.isbn

        description = (
            cmd.description
            if "description" in cmd.fields_to_update
            else book.description
        )

        # * only set the cover_url in db to None, the actual cover is still persisted in object storage
        cover_url = book.cover_url
        if "cover_url" in cmd.fields_to_update:
            assert cmd.cover_url is None
            cover_url = None

        page_count = (
            cmd.page_count if "page_count" in cmd.fields_to_update else book.page_count
        )

        published_date = (
            cmd.published_date
            if "published_date" in cmd.fields_to_update
            else book.published_date
        )

        publisher: PublisherEntity | None = book.publisher
        if "publisher_id" in cmd.fields_to_update:
            if cmd.publisher_id:
                resolved_publisher = await self._publisher_repo.find_by_id(
                    cmd.publisher_id
                )
                if resolved_publisher is None:
                    raise PublisherNotFoundError(cmd.publisher_id)
                publisher = resolved_publisher
            else:
                publisher = None
        category: CategoryEntity | None = book.category
        if "category_id" in cmd.fields_to_update:
            if cmd.category_id:
                resolved_category = await self._category_repo.find_by_id(
                    cmd.category_id
                )
                if resolved_category is None:
                    raise CategoryNotFoundError(cmd.category_id)
                category = resolved_category
            else:
                category = None

        authors: list[BookAuthorEntity] = list(book.authors)
        if "authors" in cmd.fields_to_update:
            if cmd.authors:
                now = datetime.now(UTC)
                authors = []
                for item in cmd.authors:
                    author_entity = await self._author_repo.find_by_id(item.author_id)
                    if not author_entity:
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
            else:
                authors = []

        book.update(
            title=cmd.title
            if "title" in cmd.fields_to_update and cmd.title is not None
            else book.title,
            price=cmd.price
            if "price" in cmd.fields_to_update and cmd.price is not None
            else book.price,
            stock_quantity=cmd.stock_quantity
            if "stock_quantity" in cmd.fields_to_update
            and cmd.stock_quantity is not None
            else book.stock_quantity,
            language=cmd.language
            if "language" in cmd.fields_to_update and cmd.language is not None
            else book.language,
            isbn=isbn,
            description=description,
            cover_url=cover_url,
            page_count=page_count,
            published_date=published_date,
            publisher=publisher,
            category=category,
            authors=authors,
        )
        await self._book_repo.save(book, False)
        await self._db_session.commit()

        return self._to_result(book, UpdateBookResult)
