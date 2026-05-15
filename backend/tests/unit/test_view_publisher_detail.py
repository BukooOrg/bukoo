from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.publisher_dto import (
    ViewPublisherDetailCommand,
    ViewPublisherDetailResult,
)
from app.application.use_cases.publisher.view_publisher_detail import (
    ViewPublisherDetailUseCase,
)
from app.domain.entities import PublisherEntity
from app.domain.exceptions import PublisherNotFoundError
from app.domain.repositories.publisher_repository import IPublisherRepository


def _make_publisher(
    publisher_id: str = "publisher-001",
    website: str | None = "https://example.com",
) -> PublisherEntity:
    now = datetime.now(UTC)
    return PublisherEntity(
        _id=publisher_id,
        _name="Macmillan Publishers",
        _website=website,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, publisher: PublisherEntity | None = None) -> None:
        self._publisher = publisher

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        if self._publisher and self._publisher.id == publisher_id:
            return self._publisher
        return None

    async def save(self, publisher: PublisherEntity) -> None:
        pass


@pytest.mark.unit
class TestViewPublisherDetailUseCase:
    async def test_returns_result_with_correct_fields(self) -> None:
        publisher = _make_publisher("publisher-001")
        repo = FakePublisherRepository(publisher=publisher)
        use_case = ViewPublisherDetailUseCase(
            db_session=AsyncMock(), publisher_repo=repo
        )

        result = await use_case.execute(
            ViewPublisherDetailCommand(publisher_id="publisher-001")
        )

        assert isinstance(result, ViewPublisherDetailResult)
        assert result.id == "publisher-001"
        assert result.name == "Macmillan Publishers"
        assert result.website == "https://example.com"
        assert isinstance(result.created_at, datetime)

    async def test_propagates_none_website(self) -> None:
        publisher = _make_publisher("publisher-001", website=None)
        repo = FakePublisherRepository(publisher=publisher)
        use_case = ViewPublisherDetailUseCase(
            db_session=AsyncMock(), publisher_repo=repo
        )

        result = await use_case.execute(
            ViewPublisherDetailCommand(publisher_id="publisher-001")
        )

        assert result.website is None

    async def test_raises_not_found_when_repo_returns_none(self) -> None:
        repo = FakePublisherRepository(publisher=None)
        use_case = ViewPublisherDetailUseCase(
            db_session=AsyncMock(), publisher_repo=repo
        )

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(
                ViewPublisherDetailCommand(publisher_id="nonexistent-id")
            )

    async def test_raises_not_found_when_id_does_not_match(self) -> None:
        publisher = _make_publisher("publisher-001")
        repo = FakePublisherRepository(publisher=publisher)
        use_case = ViewPublisherDetailUseCase(
            db_session=AsyncMock(), publisher_repo=repo
        )

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(
                ViewPublisherDetailCommand(publisher_id="publisher-999")
            )
