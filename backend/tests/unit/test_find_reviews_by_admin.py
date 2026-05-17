from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import FindReviewsByAdminCommand
from app.application.use_cases.review.find_reviews_by_admin import (
    FindReviewsByAdminUseCase,
)
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
    book_id: str = "book-001",
    user_id: str | None = "user-001",
    hidden_at: datetime | None = None,
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id=book_id,
        _order_item_id="item-001",
        _user_id=user_id,
        _rating=4,
        _comment="Great read.",
        _hidden_at=hidden_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _book=_make_book(book_id),
    )


def _default_query() -> QueryParams:
    return QueryParams(page=PageParams(page=1, page_size=20))


class FakeReviewRepository(IReviewRepository):
    def __init__(self, reviews: list[ReviewEntity] | None = None) -> None:
        self._reviews = reviews or []
        self.last_query: QueryParams | None = None
        self.last_filters: ReviewFilters | None = None

    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        self.last_query = query
        self.last_filters = filters

        items = self._reviews
        if filters.book_id is not None:
            items = [r for r in items if r.book_id == filters.book_id]
        if filters.user_id is not None:
            items = [r for r in items if r.user_id == filters.user_id]
        if filters.is_hidden is True:
            items = [r for r in items if r.is_hidden]
        elif filters.is_hidden is False:
            items = [r for r in items if not r.is_hidden]

        return PaginatedResult(
            items=items,
            total_items=len(items),
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def save(self, review: ReviewEntity) -> None:
        raise NotImplementedError


def _make_use_case(
    reviews: list[ReviewEntity] | None = None,
) -> tuple[FindReviewsByAdminUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(reviews=reviews)
    use_case = FindReviewsByAdminUseCase(db_session=db_session, review_repo=review_repo)
    return use_case, db_session, review_repo


def _cmd(
    book_id: str | None = None,
    user_id: str | None = None,
    is_hidden: bool | None = None,
) -> FindReviewsByAdminCommand:
    return FindReviewsByAdminCommand(
        query_params=_default_query(),
        filters=ReviewFilters(book_id=book_id, user_id=user_id, is_hidden=is_hidden),
    )


@pytest.mark.unit
class TestFindReviewsByAdminUseCase:
    async def test_returns_all_reviews_with_no_filters(self) -> None:
        reviews = [
            _make_review("r-001"),
            _make_review("r-002"),
            _make_review("r-003"),
        ]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd())

        assert result.total_items == 3
        assert len(result.items) == 3

    async def test_filters_by_book_id(self) -> None:
        reviews = [
            _make_review("r-001", book_id="book-A"),
            _make_review("r-002", book_id="book-B"),
            _make_review("r-003", book_id="book-A"),
        ]
        use_case, _, repo = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd(book_id="book-A"))

        assert result.total_items == 2
        assert repo.last_filters is not None
        assert repo.last_filters.book_id == "book-A"

    async def test_filters_by_user_id(self) -> None:
        reviews = [
            _make_review("r-001", user_id="user-A"),
            _make_review("r-002", user_id="user-B"),
        ]
        use_case, _, repo = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd(user_id="user-A"))

        assert result.total_items == 1
        assert repo.last_filters is not None
        assert repo.last_filters.user_id == "user-A"

    async def test_filters_hidden_reviews(self) -> None:
        reviews = [
            _make_review("r-001", hidden_at=datetime.now(UTC)),
            _make_review("r-002", hidden_at=None),
            _make_review("r-003", hidden_at=datetime.now(UTC)),
        ]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd(is_hidden=True))

        assert result.total_items == 2
        assert all(item.is_hidden for item in result.items)

    async def test_filters_visible_reviews(self) -> None:
        reviews = [
            _make_review("r-001", hidden_at=datetime.now(UTC)),
            _make_review("r-002", hidden_at=None),
        ]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd(is_hidden=False))

        assert result.total_items == 1
        assert not result.items[0].is_hidden

    async def test_returns_empty_list_when_no_reviews(self) -> None:
        use_case, _, _ = _make_use_case(reviews=[])

        result = await use_case.execute(_cmd())

        assert result.total_items == 0
        assert result.items == []

    async def test_result_items_include_hidden_fields(self) -> None:
        hidden_at = datetime.now(UTC)
        reviews = [_make_review("r-001", hidden_at=hidden_at)]
        use_case, _, _ = _make_use_case(reviews=reviews)

        result = await use_case.execute(_cmd())

        item = result.items[0]
        assert item.is_hidden is True
        assert item.hidden_at == hidden_at

    async def test_passes_query_params_to_repository(self) -> None:
        use_case, _, repo = _make_use_case(reviews=[])
        query = QueryParams(page=PageParams(page=2, page_size=10))
        cmd = FindReviewsByAdminCommand(
            query_params=query,
            filters=ReviewFilters(book_id=None, user_id=None, is_hidden=None),
        )

        await use_case.execute(cmd)

        assert repo.last_query is not None
        assert repo.last_query.page.page == 2
        assert repo.last_query.page.page_size == 10
