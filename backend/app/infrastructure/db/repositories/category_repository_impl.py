from __future__ import annotations

from typing import override

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import CategoryEntity
from app.domain.repositories import ICategoryRepository
from app.infrastructure.db.mappers import CategoryMapper
from app.infrastructure.db.models import BookModel, CategoryModel


class CategoryRepositoryImpl(ICategoryRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.id == category_id)
            .where(CategoryModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CategoryMapper.to_entity(model) if model else None

    @override
    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        stmt = (
            select(CategoryModel)
            .where(CategoryModel.url_slug == url_slug)
            .where(CategoryModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return CategoryMapper.to_entity(model) if model else None

    @override
    async def find_all(self, collection_id: str | None = None) -> list[CategoryEntity]:
        stmt = select(CategoryModel).where(CategoryModel.deleted_at.is_(None))
        if collection_id is not None:
            stmt = stmt.where(CategoryModel.collection_id == collection_id)
        result = await self._session.execute(stmt)
        return [CategoryMapper.to_entity(m) for m in result.scalars().all()]

    @override
    async def save(self, category: CategoryEntity) -> None:
        model = CategoryMapper.to_model(category)
        await self._session.merge(model)

    @override
    async def nullify_book_category(self, category_id: str) -> None:
        stmt = (
            update(BookModel)
            .where(BookModel.category_id == category_id)
            .where(BookModel.deleted_at.is_(None))
            .values(category_id=None)
        )
        await self._session.execute(stmt)
