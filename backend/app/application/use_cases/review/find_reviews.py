from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.review_dto import (
    BaseReviewBookItem,
    FindReviewsCommand,
    PublicReviewItem,
)
from app.core.query_params import PaginatedResult
from app.domain.exceptions import BookNotFoundError
from app.domain.repositories import IBookRepository, IReviewRepository
from app.domain.repositories.book_repository import BookStatusFilter
from app.domain.repositories.review_repository import ReviewFilters

from ..base import BaseUseCase


class FindReviewsUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo
        self._review_repo = review_repo

    @override
    async def execute(
        self, cmd: FindReviewsCommand
    ) -> PaginatedResult[PublicReviewItem]:
        book = await self._book_repo.find_by_id(
            cmd.book_id, BookStatusFilter(status="activate")
        )
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        result = await self._review_repo.find_all(
            query=cmd.query_params,
            filters=ReviewFilters(book_id=cmd.book_id, is_hidden=False),
        )

        items: list[PublicReviewItem] = []
        for r in result.items:
            assert r.book is not None
            items.append(
                PublicReviewItem(
                    id=r.id,
                    book_id=r.book_id,
                    user_id=r.user_id,
                    order_item_id=r.order_item_id,
                    rating=r.rating,
                    comment=r.comment,
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
