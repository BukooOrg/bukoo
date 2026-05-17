from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.review_dto import (
    BaseReviewBookItem,
    FindReviewsByAdminCommand,
    ReviewWithBookItem,
)
from app.core.query_params import PaginatedResult
from app.domain.repositories import IReviewRepository
from app.domain.repositories.review_repository import ReviewFilters

from ..base import BaseUseCase


class FindReviewsByAdminUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._review_repo = review_repo

    @override
    async def execute(
        self, cmd: FindReviewsByAdminCommand
    ) -> PaginatedResult[ReviewWithBookItem]:
        print(cmd.query_params)
        result = await self._review_repo.find_all(
            query=cmd.query_params,
            filters=ReviewFilters(
                book_id=cmd.filters.book_id,
                user_id=cmd.filters.user_id,
                is_hidden=cmd.filters.is_hidden,
            ),
        )

        items: list[ReviewWithBookItem] = []
        for r in result.items:
            assert r.book is not None
            items.append(
                ReviewWithBookItem(
                    id=r.id,
                    book_id=r.book_id,
                    user_id=r.user_id,
                    order_item_id=r.order_item_id,
                    rating=r.rating,
                    comment=r.comment,
                    is_hidden=r.is_hidden,
                    hidden_at=r.hidden_at,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    book=BaseReviewBookItem(
                        id=r.book.id, title=r.book.title, cover_url=r.book.cover_url
                    ),
                )
            )
        return PaginatedResult(
            items=items,
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
