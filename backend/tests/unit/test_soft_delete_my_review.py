from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import SoftDeleteMyReviewCommand
from app.application.use_cases.review.soft_delete_my_review import (
    SoftDeleteMyReviewUseCase,
)
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions.review import ReviewNotFoundError, ReviewNotOwnedError
from app.domain.repositories import IReviewRepository


def _make_review(
    review_id: str = "review-001",
    user_id: str = "user-001",
    deleted_at: datetime | None = None,
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id="book-001",
        _order_item_id="item-001",
        _user_id=user_id,
        _rating=4,
        _comment="Good read.",
        _created_at=now,
        _updated_at=now,
        _deleted_at=deleted_at,
    )


class FakeReviewRepository(IReviewRepository):
    def __init__(self, review: ReviewEntity | None = None) -> None:
        self._store: dict[str, ReviewEntity] = {}
        if review:
            self._store[review.id] = review
        self.saved: ReviewEntity | None = None

    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        return self._store.get(review_id)

    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def save(self, review: ReviewEntity) -> None:
        self.saved = review
        self._store[review.id] = review


def _make_use_case(
    review: ReviewEntity | None = None,
) -> tuple[SoftDeleteMyReviewUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(review=review)
    use_case = SoftDeleteMyReviewUseCase(db_session=db_session, review_repo=review_repo)
    return use_case, db_session, review_repo


def _cmd(
    review_id: str = "review-001",
    user_id: str = "user-001",
) -> SoftDeleteMyReviewCommand:
    return SoftDeleteMyReviewCommand(user_id=user_id, review_id=review_id)


@pytest.mark.unit
class TestSoftDeleteMyReviewUseCase:
    async def test_soft_delete_sets_deleted_at(self) -> None:
        review = _make_review()
        use_case, _, review_repo = _make_use_case(review=review)

        await use_case.execute(_cmd())

        assert review_repo.saved is not None
        assert review_repo.saved.deleted_at is not None

    async def test_commit_called_once(self) -> None:
        review = _make_review()
        use_case, db_session, _ = _make_use_case(review=review)

        await use_case.execute(_cmd())

        db_session.commit.assert_called_once()

    async def test_raises_review_not_found_when_missing(self) -> None:
        use_case, _, _ = _make_use_case(review=None)

        with pytest.raises(ReviewNotFoundError):
            await use_case.execute(_cmd(review_id="nonexistent"))

    async def test_raises_review_not_owned_when_different_user(self) -> None:
        review = _make_review(user_id="user-001")
        use_case, _, _ = _make_use_case(review=review)

        with pytest.raises(ReviewNotOwnedError):
            await use_case.execute(_cmd(user_id="user-999"))

    async def test_raises_review_not_found_for_already_deleted_review(self) -> None:
        # find_by_id filters deleted_at IS NULL, so soft-deleted records return None
        use_case, _, _ = _make_use_case(review=None)

        with pytest.raises(ReviewNotFoundError):
            await use_case.execute(_cmd(review_id="deleted-review"))
