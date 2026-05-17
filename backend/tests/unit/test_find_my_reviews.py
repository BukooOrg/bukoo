from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import FindMyReviewsCommand, ReviewWithBookItem
from app.application.use_cases.review.find_my_reviews import FindMyReviewsUseCase
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.review_entity import ReviewEntity
from app.domain.repositories import IReviewRepository
from app.domain.repositories.review_repository import ReviewFilters


def _make_book(book_id: str = "book-001") -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
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
    user_id: str = "user-001",
    hidden_at: datetime | None = None,
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id="book-001",
        _order_item_id="item-001",
        _user_id=user_id,
        _rating=4,
        _comment="Great read.",
        _hidden_at=hidden_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _book=_make_book(),
    )


def _default_query() -> QueryParams:
    return QueryParams(page=PageParams(page=1, page_size=10))


class FakeReviewRepository(IReviewRepository):
    def __init__(self, reviews: list[ReviewEntity] | None = None) -> None:
        self._reviews = reviews or []
        self.last_filters: ReviewFilters | None = None

    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        self.last_filters = filters
        items = self._reviews
        if filters.user_id is not None:
            items = [r for r in items if r.user_id == filters.user_id]
        page = query.page.page
        page_size = query.page.page_size
        offset = (page - 1) * page_size
        paged = items[offset : offset + page_size]
        return PaginatedResult(
            items=paged,
            total_items=len(items),
            page=page,
            page_size=page_size,
        )

    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def save(self, review: ReviewEntity) -> None:
        raise NotImplementedError


def _make_use_case(
    reviews: list[ReviewEntity] | None = None,
) -> tuple[FindMyReviewsUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(reviews=reviews)
    use_case = FindMyReviewsUseCase(db_session=db_session, review_repo=review_repo)
    return use_case, db_session, review_repo


def _cmd(user_id: str = "user-001") -> FindMyReviewsCommand:
    return FindMyReviewsCommand(user_id=user_id, query_params=_default_query())


@pytest.mark.unit
class TestFindMyReviewsUseCase:
    async def test_returns_reviews_for_user_with_book(self) -> None:
        reviews = [_make_review("r-001"), _make_review("r-002")]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd("user-001"))

        assert result.total_items == 2
        assert len(result.items) == 2
        assert isinstance(result.items[0], ReviewWithBookItem)
        assert result.items[0].book.id == "book-001"

    async def test_returns_only_reviews_for_matching_user(self) -> None:
        reviews = [
            _make_review("r-001", user_id="user-001"),
            _make_review("r-002", user_id="user-002"),
            _make_review("r-003", user_id="user-001"),
        ]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd("user-001"))

        assert result.total_items == 2
        assert all(item.user_id == "user-001" for item in result.items)

    async def test_includes_hidden_reviews(self) -> None:
        reviews = [
            _make_review("r-001", hidden_at=None),
            _make_review("r-002", hidden_at=datetime.now(UTC)),
        ]
        use_case, _, repo = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd("user-001"))

        assert result.total_items == 2
        assert repo.last_filters is not None
        assert repo.last_filters.is_hidden is None

    async def test_result_items_carry_is_hidden_and_hidden_at(self) -> None:
        hidden_at = datetime.now(UTC)
        reviews = [_make_review("r-001", hidden_at=hidden_at)]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd())

        assert result.items[0].is_hidden is True
        assert result.items[0].hidden_at == hidden_at

    async def test_returns_empty_list_when_user_has_no_reviews(self) -> None:
        use_case, _, _ = _make_use_case(reviews=[])

        result = await use_case.execute(_cmd())

        assert result.total_items == 0
        assert result.items == []

    async def test_pagination_returns_correct_slice(self) -> None:
        reviews = [_make_review(f"r-{i:03d}") for i in range(15)]
        use_case, _, _ = _make_use_case(reviews=reviews)
        cmd = FindMyReviewsCommand(
            user_id="user-001",
            query_params=QueryParams(page=PageParams(page=2, page_size=10)),
        )

        result = await use_case.execute(cmd)

        assert result.page == 2
        assert len(result.items) == 5
        assert result.total_items == 15
