from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.review_dto import SoftDeleteMyReviewCommand
from app.domain.exceptions.review import ReviewNotFoundError, ReviewNotOwnedError
from app.domain.repositories import IReviewRepository

from ..base import BaseUseCase


class SoftDeleteMyReviewUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._review_repo = review_repo

    @override
    async def execute(self, cmd: SoftDeleteMyReviewCommand) -> None:
        review = await self._review_repo.find_by_id(cmd.review_id)
        if review is None:
            raise ReviewNotFoundError(cmd.review_id)

        if review.user_id != cmd.user_id:
            raise ReviewNotOwnedError(cmd.review_id)

        review.soft_delete()
        await self._review_repo.save(review)
        await self._db_session.commit()
