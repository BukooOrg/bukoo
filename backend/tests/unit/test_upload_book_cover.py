from __future__ import annotations

from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.book_dto import UploadBookCoverCommand, UploadBookCoverResult
from app.application.interfaces.storage_service import IStorageService
from app.application.use_cases.book.upload_book_cover import UploadBookCoverUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import BookEntity
from app.domain.exceptions.book import BookNotFoundError
from app.domain.exceptions.storage import StorageUploadError
from app.domain.repositories.book_repository import (
    BookFilters,
    BookStatusFilter,
    IBookRepository,
)


def _make_book(book_id: str = "book-1") -> BookEntity:
    now = datetime.now(UTC)
    return BookEntity(
        _id=book_id,
        _title="The Great Gatsby",
        _price=Decimal("12.99"),
        _stock_quantity=50,
        _language="en",
        _publisher_id=None,
        _category_id=None,
        _isbn="1234567890123",
        _description=None,
        _cover_url=None,
        _page_count=180,
        _published_date=None,
        _deactivated_at=None,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _publisher=None,
        _category=None,
        _authors=[],
    )


class FakeBookRepository(IBookRepository):
    def __init__(self, book: BookEntity | None = None) -> None:
        self._books: dict[str, BookEntity] = {}
        self.saved: BookEntity | None = None
        if book is not None:
            self._books[book.id] = book

    @override
    async def find_all(
        self, query: QueryParams, filters: BookFilters
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    @override
    async def find_by_id(
        self, book_id: str, filters: BookStatusFilter
    ) -> BookEntity | None:
        return self._books.get(book_id)

    @override
    async def find_by_isbn(self, isbn: str) -> BookEntity | None:
        return None

    @override
    async def save(self, book: BookEntity) -> None:
        self._books[book.id] = book
        self.saved = book

    async def get_inventory_metrics(self, low_stock_threshold: int) -> Any:
        pass

    async def find_low_stock(
        self, query: QueryParams, threshold: int
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)

    async def find_out_of_stock(
        self, query: QueryParams
    ) -> PaginatedResult[BookEntity]:
        return PaginatedResult(items=[], total_items=0, page=1, page_size=20)


class FakeStorageService(IStorageService):
    def __init__(self, should_fail: bool = False) -> None:
        self._should_fail = should_fail
        self.uploaded_key: str | None = None
        self.uploaded_content_type: str | None = None

    @override
    async def upload(self, key: str, data: bytes, content_type: str) -> str:
        if self._should_fail:
            raise StorageUploadError(key, "test failure")
        self.uploaded_key = key
        self.uploaded_content_type = content_type
        return f"http://minio:9000/bukoo/{key}"

    @override
    async def load_once(self, key: str) -> bytes:
        return b""

    @override
    def load_stream(self, key: str) -> AsyncGenerator[bytes, None]:
        async def _gen() -> AsyncGenerator[bytes, None]:
            yield b""

        return _gen()

    @override
    async def exists(self, key: str) -> bool:
        return self.uploaded_key == key

    @override
    async def delete(self, key: str) -> None:
        pass

    @override
    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        return f"http://minio:9000/bukoo/{key}?expires={expires_in}"


@pytest.mark.unit
class TestUploadBookCoverUseCase:
    async def test_returns_result_with_correct_cover_url(self) -> None:
        book = _make_book("book-1")
        repo = FakeBookRepository(book)
        storage = FakeStorageService()
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        result = await use_case.execute(
            UploadBookCoverCommand(
                book_id="book-1",
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        assert isinstance(result, UploadBookCoverResult)
        assert result.cover_url == "pub/covers/book-1"

    async def test_storage_upload_receives_correct_key_and_content_type(self) -> None:
        book = _make_book("book-1")
        repo = FakeBookRepository(book)
        storage = FakeStorageService()
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        await use_case.execute(
            UploadBookCoverCommand(
                book_id="book-1",
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        assert storage.uploaded_key == "pub/covers/book-1"
        assert storage.uploaded_content_type == "image/jpeg"

    async def test_commit_called_once(self) -> None:
        book = _make_book("book-1")
        repo = FakeBookRepository(book)
        storage = FakeStorageService()
        db_session = AsyncMock()
        use_case = UploadBookCoverUseCase(
            db_session=db_session, book_repo=repo, storage_svc=storage
        )

        await use_case.execute(
            UploadBookCoverCommand(
                book_id="book-1",
                file_data=b"fake image bytes",
                content_type="image/jpeg",
            )
        )

        db_session.commit.assert_called_once()

    async def test_raises_book_not_found_when_missing(self) -> None:
        repo = FakeBookRepository()
        storage = FakeStorageService()
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        with pytest.raises(BookNotFoundError):
            await use_case.execute(
                UploadBookCoverCommand(
                    book_id="nonexistent",
                    file_data=b"fake image bytes",
                    content_type="image/jpeg",
                )
            )

    async def test_raises_storage_upload_error_on_upload_failure(self) -> None:
        book = _make_book("book-1")
        repo = FakeBookRepository(book)
        storage = FakeStorageService(should_fail=True)
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        with pytest.raises(StorageUploadError):
            await use_case.execute(
                UploadBookCoverCommand(
                    book_id="book-1",
                    file_data=b"fake image bytes",
                    content_type="image/jpeg",
                )
            )

    async def test_re_upload_uses_same_deterministic_key(self) -> None:
        book = _make_book("book-1")
        repo = FakeBookRepository(book)
        storage = FakeStorageService()
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        await use_case.execute(
            UploadBookCoverCommand(
                book_id="book-1",
                file_data=b"first cover",
                content_type="image/jpeg",
            )
        )
        result = await use_case.execute(
            UploadBookCoverCommand(
                book_id="book-1",
                file_data=b"second cover",
                content_type="image/png",
            )
        )

        assert result.cover_url == "pub/covers/book-1"
        assert storage.uploaded_key == "pub/covers/book-1"

    async def test_soft_deleted_book_treated_as_not_found(self) -> None:
        repo = FakeBookRepository()  # empty — simulates repo hiding deleted record
        storage = FakeStorageService()
        use_case = UploadBookCoverUseCase(
            db_session=AsyncMock(), book_repo=repo, storage_svc=storage
        )

        with pytest.raises(BookNotFoundError):
            await use_case.execute(
                UploadBookCoverCommand(
                    book_id="deleted-book",
                    file_data=b"fake image bytes",
                    content_type="image/jpeg",
                )
            )
