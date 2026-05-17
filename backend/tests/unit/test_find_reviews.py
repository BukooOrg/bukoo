from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import FindReviewsCommand, PublicReviewItem
from app.application.use_cases.review.find_reviews import FindReviewsUseCase
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions import BookNotFoundError
from app.domain.repositories import IBookRepository, IReviewRepository
from app.domain.repositories.book_repository import BookFilters, BookStatusFilter
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
    hidden_at: datetime | None = None,
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id=review_id,
        _book_id=book_id,
        _order_item_id="item-001",
        _user_id="user-001",
        _rating=4,
        _comment="Great read.",
        _hidden_at=hidden_at,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _book=_make_book(book_id),
    )


def _default_query() -> QueryParams:
    return QueryParams(page=PageParams(page=1, page_size=10))


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._book = book

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        if self._book and self._book.id == book_id:
            return self._book
        return None

    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        raise NotImplementedError

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        raise NotImplementedError

    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = True
    ) -> None:
        raise NotImplementedError


class FakeReviewRepository(IReviewRepository):
    def __init__(self, reviews: list[ReviewEntity] | None = None) -> None:
        self._reviews = reviews or []
        self.last_filters: ReviewFilters | None = None

    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        self.last_filters = filters
        items = self._reviews
        if filters.book_id is not None:
            items = [r for r in items if r.book_id == filters.book_id]
        if filters.is_hidden is False:
            items = [r for r in items if not r.is_hidden]
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
    book: BookEntity | None = None,
    reviews: list[ReviewEntity] | None = None,
) -> tuple[FindReviewsUseCase, AsyncMock, FakeBookRepository, FakeReviewRepository]:
    db_session = AsyncMock()
    book_repo = FakeBookRepository(book=book)
    review_repo = FakeReviewRepository(reviews=reviews)
    use_case = FindReviewsUseCase(
        db_session=db_session, book_repo=book_repo, review_repo=review_repo
    )
    return use_case, db_session, book_repo, review_repo


def _cmd(book_id: str = "book-001") -> FindReviewsCommand:
    return FindReviewsCommand(book_id=book_id, query_params=_default_query())


@pytest.mark.unit
class TestFindReviewsUseCase:
    async def test_returns_paginated_reviews_with_book(self) -> None:
        book = _make_book("book-001")
        reviews = [_make_review("r-001"), _make_review("r-002")]
        use_case, _, _, _ = _make_use_case(book=book, reviews=reviews)

        result = await use_case.execute(_cmd("book-001"))

        assert result.total_items == 2
        assert len(result.items) == 2
        assert isinstance(result.items[0], PublicReviewItem)
        assert result.items[0].book.id == "book-001"
        assert result.items[0].book.title == "Test Book"

    async def test_raises_book_not_found_when_book_missing(self) -> None:
        use_case, _, _, _ = _make_use_case(book=None)

        with pytest.raises(BookNotFoundError):
            await use_case.execute(_cmd("nonexistent-book"))

    async def test_excludes_hidden_reviews(self) -> None:
        book = _make_book("book-001")
        reviews = [
            _make_review("r-001", hidden_at=None),
            _make_review("r-002", hidden_at=datetime.now(UTC)),
        ]
        use_case, _, _, repo = _make_use_case(book=book, reviews=reviews)

        result = await use_case.execute(_cmd("book-001"))

        assert result.total_items == 1
        assert repo.last_filters is not None
        assert repo.last_filters.is_hidden is False

    async def test_returns_empty_when_no_visible_reviews(self) -> None:
        book = _make_book("book-001")
        use_case, _, _, _ = _make_use_case(book=book, reviews=[])

        result = await use_case.execute(_cmd("book-001"))

        assert result.total_items == 0
        assert result.items == []

    async def test_pagination_returns_correct_slice(self) -> None:
        book = _make_book("book-001")
        reviews = [_make_review(f"r-{i:03d}") for i in range(15)]
        use_case, _, _, _ = _make_use_case(book=book, reviews=reviews)
        cmd = FindReviewsCommand(
            book_id="book-001",
            query_params=QueryParams(page=PageParams(page=2, page_size=10)),
        )

        result = await use_case.execute(cmd)

        assert result.page == 2
        assert result.page_size == 10
        assert len(result.items) == 5
        assert result.total_items == 15

    async def test_passes_is_hidden_false_filter_to_repo(self) -> None:
        book = _make_book("book-001")
        use_case, _, _, repo = _make_use_case(book=book, reviews=[])

        await use_case.execute(_cmd("book-001"))

        assert repo.last_filters is not None
        assert repo.last_filters.book_id == "book-001"
        assert repo.last_filters.is_hidden is False
