from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import ColumnElement, and_, delete, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, selectinload

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity
from app.domain.repositories import IBookRepository
from app.domain.repositories.book_repository import BookFilters, BookStatusFilter
from app.infrastructure.db.mappers import BookAuthorMapper, BookMapper
from app.infrastructure.db.models import AuthorModel, BookAuthorModel, BookModel
from app.infrastructure.db.models.category_model import CategoryModel


class BookRepositoryImpl(IBookRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "title": BookModel.title,
        "price": BookModel.price,
        "published_date": BookModel.published_date,
        "created_at": BookModel.created_at,
        "updated_at": BookModel.updated_at,
    }

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        conditions: list[ColumnElement[bool]] = [
            BookModel.deleted_at.is_(None),
        ]
        needs_category_join = False

        if filters.search:
            fts = BookModel.search_vector.op("@@")(
                func.plainto_tsquery("english", filters.search)
            )
            author_name_match = exists(
                select(1)
                .select_from(BookAuthorModel)
                .join(AuthorModel, AuthorModel.id == BookAuthorModel.author_id)
                .where(BookAuthorModel.book_id == BookModel.id)
                .where(AuthorModel.name.ilike(f"%{filters.search}%"))
                .where(AuthorModel.deleted_at.is_(None))
            )
            conditions.append(or_(fts, author_name_match))

        if filters.category_id:
            conditions.append(BookModel.category_id == filters.category_id)

        if filters.publisher_id:
            conditions.append(BookModel.publisher_id == filters.publisher_id)

        if filters.author_id:
            author_assoc = exists(
                select(1)
                .select_from(BookAuthorModel)
                .where(BookAuthorModel.book_id == BookModel.id)
                .where(BookAuthorModel.author_id == filters.author_id)
            )
            conditions.append(author_assoc)

        if filters.collection_id:
            needs_category_join = True
            conditions.append(CategoryModel.collection_id == filters.collection_id)

        if filters.language:
            conditions.append(
                func.lower(BookModel.language) == filters.language.lower()
            )

        if filters.price_min is not None:
            conditions.append(BookModel.price >= filters.price_min)

        if filters.price_max is not None:
            conditions.append(BookModel.price <= filters.price_max)

        if filters.in_stock:
            conditions.append(BookModel.stock_quantity > 0)

        if filters.status == "activate":
            conditions.append(BookModel.deactivated_at.is_(None))
        elif filters.status == "deactivate":
            conditions.append(BookModel.deactivated_at.is_not(None))

        where_clause = and_(*conditions)

        base_stmt = select(BookModel)
        if needs_category_join:
            base_stmt = base_stmt.join(
                CategoryModel,
                BookModel.category_id == CategoryModel.id,
                isouter=True,
            )

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(
                    base_stmt.where(where_clause).subquery()
                )
            )
        ).scalar_one()

        order_clauses = [
            self.SORTABLE_FIELDS[s.field].asc()
            if s.direction == "asc"
            else self.SORTABLE_FIELDS[s.field].desc()
            for s in query.sorts
            if s.field in self.SORTABLE_FIELDS
        ]
        if not order_clauses:
            order_clauses = [BookModel.created_at.desc()]

        models = (
            (
                await self._session.execute(
                    base_stmt.where(where_clause)
                    .options(
                        selectinload(BookModel.publisher),
                        selectinload(BookModel.category),
                        selectinload(BookModel.author_associations).selectinload(
                            BookAuthorModel.author
                        ),
                    )
                    .order_by(*order_clauses)
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[BookMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    @override
    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        conditions: list[ColumnElement[bool]] = [
            BookModel.deleted_at.is_(None),
        ]

        if filters.status == "activate":
            conditions.append(BookModel.deactivated_at.is_(None))
        elif filters.status == "deactivate":
            conditions.append(BookModel.deactivated_at.is_not(None))

        where_clause = and_(*conditions)

        stmt = (
            select(BookModel)
            .where(BookModel.id == book_id)
            .where(where_clause)
            .options(
                selectinload(BookModel.publisher),
                selectinload(BookModel.category),
                selectinload(BookModel.author_associations).selectinload(
                    BookAuthorModel.author
                ),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return BookMapper.to_entity(model) if model else None

    @override
    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        stmt = (
            select(BookModel)
            .where(BookModel.isbn == isbn)
            .where(BookModel.deleted_at.is_(None))
            .options(
                selectinload(BookModel.publisher),
                selectinload(BookModel.category),
                selectinload(BookModel.author_associations).selectinload(
                    BookAuthorModel.author
                ),
            )
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return BookMapper.to_entity(model) if model else None

    @override
    async def save(self, book: BookEntity) -> None:
        model = BookMapper.to_model(book)
        await self._session.merge(model)

        await self._session.execute(
            delete(BookAuthorModel).where(BookAuthorModel.book_id == book.id)
        )
        for book_author_entity in book.authors:
            book_author_model = BookAuthorMapper.to_model(book_author_entity)
            self._session.add(book_author_model)
