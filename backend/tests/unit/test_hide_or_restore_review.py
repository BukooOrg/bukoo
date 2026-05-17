from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import HideOrRestoreReviewCommand
from app.application.use_cases.review.hide_or_restore_review import (
    HideOrRestoreReviewUseCase,
)
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions.review import ReviewNotFoundError
from app.domain.repositories import IReviewRepository
from app.domain.repositories.review_repository import ReviewFilters


def _make_book() -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id="book-001",
        _title="Test Book",
        _price=Decimal("9.99"),
        _stock_quantity=10,
        _language="en",
        _publisher_id=None,
        _category_id=None,
        _isbn=None,
        _description=None,
        _cover_url=None,
        _page_count=None,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_review(
    review_id: str = "review-001",
    hidden_at: datetime | None = None,
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id="book-001",
        _order_item_id="item-001",
        _user_id="user-001",
        _rating=4,
        _comment="Great read.",
        _hidden_at=hidden_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _book=_make_book(),
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

    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        raise NotImplementedError

    async def save(self, review: ReviewEntity) -> None:
        self.saved = review
        self._store[review.id] = review


def _make_use_case(
    review: ReviewEntity | None = None,
) -> tuple[HideOrRestoreReviewUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(review=review)
    use_case = HideOrRestoreReviewUseCase(
        db_session=db_session, review_repo=review_repo
    )
    return use_case, db_session, review_repo


def _cmd(
    review_id: str = "review-001",
    is_hidden: bool = True,
) -> HideOrRestoreReviewCommand:
    return HideOrRestoreReviewCommand(review_id=review_id, is_hidden=is_hidden)


@pytest.mark.unit
class TestHideOrRestoreReviewUseCase:
    async def test_hide_sets_is_hidden_true_and_hidden_at(self) -> None:
        review = _make_review()
        use_case, _, review_repo = _make_use_case(review=review)

        result = await use_case.execute(_cmd(is_hidden=True))

        assert result.is_hidden is True
        assert result.hidden_at is not None
        assert review_repo.saved is not None
        assert review_repo.saved.is_hidden is True

    async def test_restore_sets_is_hidden_false_and_hidden_at_none(self) -> None:
        review = _make_review(hidden_at=datetime.now(UTC))
        use_case, _, review_repo = _make_use_case(review=review)

        result = await use_case.execute(_cmd(is_hidden=False))

        assert result.is_hidden is False
        assert result.hidden_at is None
        assert review_repo.saved is not None
        assert review_repo.saved.is_hidden is False

    async def test_commit_called_once(self) -> None:
        review = _make_review()
        use_case, db_session, _ = _make_use_case(review=review)

        await use_case.execute(_cmd())

        db_session.commit.assert_called_once()

    async def test_raises_review_not_found_when_missing(self) -> None:
        use_case, _, _ = _make_use_case(review=None)

        with pytest.raises(ReviewNotFoundError):
            await use_case.execute(_cmd(review_id="nonexistent"))

    async def test_hide_already_hidden_review_is_idempotent(self) -> None:
        already_hidden_at = datetime(2026, 1, 1, tzinfo=UTC)
        review = _make_review(hidden_at=already_hidden_at)
        use_case, _, review_repo = _make_use_case(review=review)

        result = await use_case.execute(_cmd(is_hidden=True))

        assert result.is_hidden is True
        assert result.hidden_at is not None
        # hidden_at updated to a new timestamp
        assert result.hidden_at != already_hidden_at

    async def test_restore_already_visible_review_is_idempotent(self) -> None:
        review = _make_review(hidden_at=None)
        use_case, _, review_repo = _make_use_case(review=review)

        result = await use_case.execute(_cmd(is_hidden=False))

        assert result.is_hidden is False
        assert result.hidden_at is None
