from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.review_dto import CreateReviewCommand, CreateReviewResult
from app.application.use_cases.review.create_review import CreateReviewUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.book_entity import BookEntity
from app.domain.entities.order_item_entity import OrderItemEntity
from app.domain.entities.review_entity import ReviewEntity
from app.domain.exceptions import BookNotFoundError
from app.domain.exceptions.review import (
    ReviewAlreadyExistsError,
    ReviewNotEligibleError,
)
from app.domain.repositories import IBookRepository, IOrderRepository, IReviewRepository
from app.domain.repositories.book_repository import BookStatusFilter
from app.domain.repositories.order_repository import OrderFilters
from app.domain.repositories.review_repository import ReviewFilters


def _make_book(book_id: str = "book-001") -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="Test Book",
        _price=Decimal("29.99"),
        _stock_quantity=10,
        _language="English",
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


def _make_order_item(
    item_id: str = "item-001", book_id: str = "book-001"
) -> OrderItemEntity:
    now = datetime.now(UTC)
    return OrderItemEntity(
        _id=item_id,
        _order_id="order-001",
        _book_id=book_id,
        _book_title="Test Book",
        _unit_price=Decimal("29.99"),
        _quantity=1,
        _line_total=Decimal("29.99"),
        _created_at=now,
        _updated_at=now,
    )


def _make_review(
    order_item_id: str = "item-001", book_id: str = "book-001"
) -> ReviewEntity:
    now = datetime.now(UTC)
    return ReviewEntity(
        _id="review-001",
        _book_id=book_id,
        _order_item_id=order_item_id,
        _user_id="user-001",
        _rating=5,
        _comment="Great book!",
        _hidden_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._book = book

    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        if self._book and self._book.id == book_id:
            return self._book
        return None

    async def find_all(self, query: object, filters: object) -> object:  # type: ignore[override]
        raise NotImplementedError

    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        raise NotImplementedError

    async def save(
        self, book: BookEntity, should_skip_book_authors: bool = True
    ) -> None:
        raise NotImplementedError


class FakeOrderRepository(IOrderRepository):
    def __init__(self, order_item: OrderItemEntity | None = None) -> None:
        self._order_item = order_item

    async def find_delivered_order_item(
        self, user_id: str, order_item_id: str, book_id: str
    ) -> OrderItemEntity | None:
        if self._order_item and self._order_item.id == order_item_id:
            return self._order_item
        return None

    async def find_by_id(self, order_id: str) -> object:  # type: ignore[override]
        raise NotImplementedError

    async def save(self, order: object, should_skip_items: bool = True) -> None:  # type: ignore[override]
        raise NotImplementedError

    async def find_all(self, query: object, filters: OrderFilters) -> object:  # type: ignore[override]
        raise NotImplementedError


class FakeReviewRepository(IReviewRepository):
    def __init__(self, existing: ReviewEntity | None = None) -> None:
        self._existing = existing
        self.saved: ReviewEntity | None = None

    async def find_by_id(self, review_id: str) -> ReviewEntity | None:
        raise NotImplementedError

    async def find_by_order_item_id(self, order_item_id: str) -> ReviewEntity | None:
        if self._existing and self._existing.order_item_id == order_item_id:
            return self._existing
        return None

    async def find_all(
        self, query: QueryParams, filters: ReviewFilters
    ) -> PaginatedResult[ReviewEntity]:
        raise NotImplementedError

    async def save(self, review: ReviewEntity) -> None:
        self.saved = review


def _make_use_case(
    book: BookEntity | None = None,
    order_item: OrderItemEntity | None = None,
    existing_review: ReviewEntity | None = None,
) -> tuple[CreateReviewUseCase, AsyncMock, FakeReviewRepository]:
    db_session = AsyncMock()
    review_repo = FakeReviewRepository(existing=existing_review)
    use_case = CreateReviewUseCase(
        db_session=db_session,
        book_repo=FakeBookRepository(book=book),
        order_repo=FakeOrderRepository(order_item=order_item),
        review_repo=review_repo,
    )
    return use_case, db_session, review_repo


def _valid_command(
    book_id: str = "book-001",
    order_item_id: str = "item-001",
    rating: int | None = 5,
    comment: str | None = None,
) -> CreateReviewCommand:
    return CreateReviewCommand(
        user_id="user-001",
        book_id=book_id,
        order_item_id=order_item_id,
        rating=rating,
        comment=comment,
    )


@pytest.mark.unit
class TestCreateReviewUseCase:
    async def test_creates_review_with_rating_and_comment(self) -> None:
        book = _make_book()
        order_item = _make_order_item()
        use_case, db_session, review_repo = _make_use_case(
            book=book, order_item=order_item
        )
        cmd = _valid_command(rating=5, comment="Loved it!")

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateReviewResult)
        assert result.book_id == "book-001"
        assert result.user_id == "user-001"
        assert result.order_item_id == "item-001"
        assert result.rating == 5
        assert result.comment == "Loved it!"
        assert review_repo.saved is not None
        db_session.commit.assert_called_once()

    async def test_creates_review_with_rating_only(self) -> None:
        book = _make_book()
        order_item = _make_order_item()
        use_case, db_session, _ = _make_use_case(book=book, order_item=order_item)
        cmd = _valid_command(rating=4, comment=None)

        result = await use_case.execute(cmd)

        assert result.rating == 4
        assert result.comment is None

    async def test_creates_review_with_comment_only(self) -> None:
        book = _make_book()
        order_item = _make_order_item()
        use_case, db_session, _ = _make_use_case(book=book, order_item=order_item)
        cmd = _valid_command(rating=None, comment="Good read.")

        result = await use_case.execute(cmd)

        assert result.rating is None
        assert result.comment == "Good read."

    async def test_raises_book_not_found_when_book_missing(self) -> None:
        order_item = _make_order_item()
        use_case, _, _ = _make_use_case(book=None, order_item=order_item)
        cmd = _valid_command()

        with pytest.raises(BookNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_review_not_eligible_when_no_delivered_order_item(
        self,
    ) -> None:
        book = _make_book()
        use_case, _, _ = _make_use_case(book=book, order_item=None)
        cmd = _valid_command()

        with pytest.raises(ReviewNotEligibleError):
            await use_case.execute(cmd)

    async def test_raises_review_already_exists_when_duplicate(self) -> None:
        book = _make_book()
        order_item = _make_order_item()
        existing = _make_review()
        use_case, _, _ = _make_use_case(
            book=book, order_item=order_item, existing_review=existing
        )
        cmd = _valid_command()

        with pytest.raises(ReviewAlreadyExistsError):
            await use_case.execute(cmd)
