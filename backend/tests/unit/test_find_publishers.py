from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.publisher_dto import (
    BasePublisherResult,
    FindPublishersCommand,
)
from app.application.use_cases.publisher.find_publishers import FindPublishersUseCase
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities import PublisherEntity
from app.domain.repositories.publisher_repository import IPublisherRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _make_publisher(
    publisher_id: str = "pub-001",
    name: str = "Macmillan Publishers",
    website: str | None = "https://www.macmillan.com",
) -> PublisherEntity:
    now = _now()
    return PublisherEntity(
        _id=publisher_id,
        _name=name,
        _website=website,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_paginated(
    publishers: list[PublisherEntity],
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResult[PublisherEntity]:
    return PaginatedResult(
        items=publishers,
        total_items=len(publishers),
        page=page,
        page_size=page_size,
    )


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, result: PaginatedResult[PublisherEntity] | None = None) -> None:
        self._result: PaginatedResult[PublisherEntity] = result or PaginatedResult(
            items=[], total_items=0, page=1, page_size=20
        )
        self.last_query: QueryParams | None = None

    async def find_all(self, query: QueryParams) -> PaginatedResult[PublisherEntity]:
        self.last_query = query
        return self._result

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        return None

    async def save(self, publisher: PublisherEntity) -> None:
        pass


@pytest.mark.unit
class TestFindPublishersUseCase:
    async def test_returns_paginated_result_with_correct_fields(self) -> None:
        now = _now()
        publisher = PublisherEntity(
            _id="pub-001",
            _name="Macmillan Publishers",
            _website="https://www.macmillan.com",
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )
        repo = FakePublisherRepository(result=_make_paginated([publisher]))
        use_case = FindPublishersUseCase(db_session=AsyncMock(), publisher_repo=repo)

        result = await use_case.execute(
            FindPublishersCommand(query_params=QueryParams())
        )

        assert isinstance(result, PaginatedResult)
        assert len(result.items) == 1
        item = result.items[0]
        assert isinstance(item, BasePublisherResult)
        assert item.id == "pub-001"
        assert item.name == "Macmillan Publishers"
        assert item.website == "https://www.macmillan.com"
        assert item.created_at == now

    async def test_returns_empty_items_when_no_publishers(self) -> None:
        repo = FakePublisherRepository()
        use_case = FindPublishersUseCase(db_session=AsyncMock(), publisher_repo=repo)

        result = await use_case.execute(
            FindPublishersCommand(query_params=QueryParams())
        )

        assert isinstance(result, PaginatedResult)
        assert result.items == []
        assert result.total_items == 0

    async def test_returns_correct_pagination_fields(self) -> None:
        publishers = [_make_publisher(f"pub-{i}") for i in range(3)]
        repo = FakePublisherRepository(
            result=PaginatedResult(
                items=publishers, total_items=15, page=2, page_size=5
            )
        )
        use_case = FindPublishersUseCase(db_session=AsyncMock(), publisher_repo=repo)

        result = await use_case.execute(
            FindPublishersCommand(
                query_params=QueryParams(page=PageParams(page=2, page_size=5))
            )
        )

        assert result.page == 2
        assert result.page_size == 5
        assert result.total_items == 15

    async def test_propagates_none_website(self) -> None:
        publisher = _make_publisher(website=None)
        repo = FakePublisherRepository(result=_make_paginated([publisher]))
        use_case = FindPublishersUseCase(db_session=AsyncMock(), publisher_repo=repo)

        result = await use_case.execute(
            FindPublishersCommand(query_params=QueryParams())
        )

        assert result.items[0].website is None
