from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import UpdateMyReviewCommand, UpdateMyReviewResult
from app.application.use_cases.review.update_my_review import UpdateMyReviewUseCase
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions.review import ReviewNotFoundError, ReviewNotOwnedError
from app.domain.repositories import IReviewRepository


def _make_review(
    review_id: str = "review-001",
    user_id: str = "user-001",
    rating: int | None = 5,
    comment: str | None = "Great book!",
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id="book-001",
        _order_item_id="item-001",
        _user_id=user_id,
        _rating=rating,
        _comment=comment,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
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
) -> tuple[UpdateMyReviewUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(review=review)
    use_case = UpdateMyReviewUseCase(db_session=db_session, review_repo=review_repo)
    return use_case, db_session, review_repo


def _cmd(
    review_id: str = "review-001",
    user_id: str = "user-001",
    rating: int | None = None,
    comment: str | None = None,
    fields_to_update: frozenset[str] = frozenset({"rating"}),
) -> UpdateMyReviewCommand:
    return UpdateMyReviewCommand(
        user_id=user_id,
        review_id=review_id,
        rating=rating,
        comment=comment,
        fields_to_update=fields_to_update,
    )


@pytest.mark.unit
class TestUpdateMyReviewUseCase:
    async def test_updates_both_rating_and_comment(self) -> None:
        review = _make_review(rating=5, comment="Old comment")
        use_case, db_session, review_repo = _make_use_case(review=review)
        cmd = _cmd(
            rating=4,
            comment="Updated comment",
            fields_to_update=frozenset({"rating", "comment"}),
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateMyReviewResult)
        assert result.rating == 4
        assert result.comment == "Updated comment"
        assert review_repo.saved is not None
        db_session.commit.assert_called_once()

    async def test_updates_rating_only_preserves_comment(self) -> None:
        review = _make_review(rating=5, comment="Keep this comment")
        use_case, _, _ = _make_use_case(review=review)
        cmd = _cmd(rating=2, fields_to_update=frozenset({"rating"}))

        result = await use_case.execute(cmd)

        assert result.rating == 2
        assert result.comment == "Keep this comment"

    async def test_updates_comment_only_preserves_rating(self) -> None:
        review = _make_review(rating=3, comment="Old")
        use_case, _, _ = _make_use_case(review=review)
        cmd = _cmd(comment="New comment", fields_to_update=frozenset({"comment"}))

        result = await use_case.execute(cmd)

        assert result.rating == 3
        assert result.comment == "New comment"

    async def test_clears_rating_when_explicitly_set_to_none(self) -> None:
        review = _make_review(rating=4, comment="Still here")
        use_case, _, _ = _make_use_case(review=review)
        cmd = _cmd(rating=None, fields_to_update=frozenset({"rating"}))

        result = await use_case.execute(cmd)

        assert result.rating is None
        assert result.comment == "Still here"

    async def test_raises_review_not_found_when_missing(self) -> None:
        use_case, _, _ = _make_use_case(review=None)
        cmd = _cmd(review_id="nonexistent")

        with pytest.raises(ReviewNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_review_not_owned_when_different_user(self) -> None:
        review = _make_review(user_id="user-001")
        use_case, _, _ = _make_use_case(review=review)
        cmd = _cmd(user_id="user-999", fields_to_update=frozenset({"rating"}))

        with pytest.raises(ReviewNotOwnedError):
            await use_case.execute(cmd)
