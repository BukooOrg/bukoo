from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.category_dto import BaseCategoryResult
from app.application.dtos.collection_dto import (
    BaseCollectionResult,
    FindCollectionsResult,
)
from app.domain.repositories.collection_repository import ICollectionRepository

from ..base import BaseUseCase


class FindCollectionsUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        collection_repo: ICollectionRepository,
    ) -> None:
        super().__init__(db_session)
        self._collection_repo = collection_repo

    @override
    async def execute(self) -> FindCollectionsResult:
        collections = await self._collection_repo.find_all()

        collection_results = [
            BaseCollectionResult(
                id=c.id,
                name=c.name,
                url_slug=c.url_slug,
                created_at=c.created_at,
                categories=[
                    BaseCategoryResult(
                        id=cat.id,
                        collection_id=cat.collection_id,
                        name=cat.name,
                        url_slug=cat.url_slug,
                        created_at=cat.created_at,
                    )
                    for cat in c.categories
                ],
            )
            for c in collections
        ]

        return FindCollectionsResult(collections=collection_results)
