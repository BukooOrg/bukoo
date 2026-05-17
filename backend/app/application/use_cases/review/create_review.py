from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.review_dto import CreateReviewCommand, CreateReviewResult
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions import BookNotFoundError
from app.domain.exceptions.review import (
    ReviewAlreadyExistsError,
    ReviewNotEligibleError,
)
from app.domain.repositories import IBookRepository, IOrderRepository, IReviewRepository
from app.domain.repositories.book_repository import BookStatusFilter

from ..base import BaseUseCase


class CreateReviewUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        order_repo: IOrderRepository,
        review_repo: IReviewRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo
        self._order_repo = order_repo
        self._review_repo = review_repo

    @override
    async def execute(self, cmd: CreateReviewCommand) -> CreateReviewResult:
        book = await self._book_repo.find_by_id(
            cmd.book_id, BookStatusFilter(status="activate")
        )
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        order_item = await self._order_repo.find_delivered_order_item(
            user_id=cmd.user_id,
            order_item_id=cmd.order_item_id,
            book_id=cmd.book_id,
        )
        if order_item is None:
            raise ReviewNotEligibleError(cmd.order_item_id)

        existing = await self._review_repo.find_by_order_item_id(cmd.order_item_id)
        if existing is not None:
            raise ReviewAlreadyExistsError(cmd.order_item_id)

        now = datetime.now(UTC)
        review = ReviewEntity(
            _id=str(uuid7()),
            _book_id=cmd.book_id,
            _order_item_id=cmd.order_item_id,
            _user_id=cmd.user_id,
            _rating=cmd.rating,
            _comment=cmd.comment,
            _hidden_at=None,
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )

        await self._review_repo.save(review)
        await self._db_session.commit()

        return CreateReviewResult(
            id=review.id,
            book_id=review.book_id,
            user_id=review.user_id,
            order_item_id=review.order_item_id,
            rating=review.rating,
            comment=review.comment,
            created_at=review.created_at,
            updated_at=review.updated_at,
        )
