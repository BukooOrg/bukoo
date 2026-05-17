from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.review_dto import UpdateMyReviewCommand, UpdateMyReviewResult
from app.domain.exceptions.review import ReviewNotFoundError, ReviewNotOwnedError
from app.domain.repositories import IReviewRepository

from ..base import BaseUseCase


class UpdateMyReviewUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._review_repo = review_repo

    @override
    async def execute(self, cmd: UpdateMyReviewCommand) -> UpdateMyReviewResult:
        review = await self._review_repo.find_by_id(cmd.review_id)
        if review is None:
            raise ReviewNotFoundError(cmd.review_id)

        if review.user_id != cmd.user_id:
            raise ReviewNotOwnedError(cmd.review_id)

        new_rating = cmd.rating if "rating" in cmd.fields_to_update else review.rating
        new_comment = (
            cmd.comment if "comment" in cmd.fields_to_update else review.comment
        )

        review.update(rating=new_rating, comment=new_comment)

        await self._review_repo.save(review)
        await self._db_session.commit()

        return UpdateMyReviewResult(
            id=review.id,
            book_id=review.book_id,
            user_id=review.user_id,
            order_item_id=review.order_item_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
