from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.review_dto import (
    BaseReviewBookItem,
    HideOrRestoreReviewCommand,
    HideOrRestoreReviewResult,
)
from app.domain.exceptions.review import ReviewNotFoundError
from app.domain.repositories import IReviewRepository

from ..base import BaseUseCase


class HideOrRestoreReviewUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._review_repo = review_repo

    @override
    async def execute(
        self, cmd: HideOrRestoreReviewCommand
    ) -> HideOrRestoreReviewResult:
        review = await self._review_repo.find_by_id(cmd.review_id)
        if review is None:
            raise ReviewNotFoundError(cmd.review_id)

        if cmd.is_hidden:
            review.hide()
        else:
            review.restore()
        await self._review_repo.save(review)
        await self._db_session.commit()

        assert review.book is not None
        return HideOrRestoreReviewResult(
            id=review.id,
            book_id=review.book_id,
            user_id=review.user_id,
            order_item_id=review.order_item_id,
            rating=review.rating,
            comment=review.comment,
            is_hidden=review.is_hidden,
            hidden_at=review._hidden_at,
            created_at=review.created_at,
            updated_at=review.updated_at,
            book=BaseReviewBookItem(
                id=review.book.id,
                title=review.book.title,
                cover_url=review.book.cover_url,
            ),
        )
