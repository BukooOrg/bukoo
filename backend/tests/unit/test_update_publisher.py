from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.publisher_dto import (
    UpdatePublisherCommand,
    UpdatePublisherResult,
)
from app.application.use_cases.publisher.update_publisher import UpdatePublisherUseCase
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities import PublisherEntity
from app.domain.exceptions import PublisherNotFoundError
from app.domain.repositories.publisher_repository import IPublisherRepository


def _make_publisher(publisher_id: str = "pub-001") -> PublisherEntity:
    now = datetime.now(UTC)
    return PublisherEntity(
        _id=publisher_id,
        _name="Penguin Random House",
        _website="https://penguinrandomhouse.com",
        _created_at=now,
        _updated_at=now,
    )


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, publisher: PublisherEntity | None = None) -> None:
        self._publisher: PublisherEntity | None = publisher
        self.saved: PublisherEntity | None = None

    async def find_all(self, query: QueryParams) -> PaginatedResult[PublisherEntity]:
        return PaginatedResult(
            items=[],
            total_items=0,
            page=query.page.page,
            page_size=query.page.page_size,
        )

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        if self._publisher and self._publisher.id == publisher_id:
            return self._publisher
        return None

    async def save(self, publisher: PublisherEntity) -> None:
        self.saved = publisher


@pytest.mark.unit
class TestUpdatePublisherUseCase:
    async def test_updates_name_and_website(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = UpdatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = UpdatePublisherCommand(
            publisher_id="pub-001",
            name="New Name",
            website="https://example.com",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdatePublisherResult)
        assert result.id == "pub-001"
        assert result.name == "New Name"
        assert result.website == "https://example.com"
        assert isinstance(result.created_at, datetime)
        db_session.commit.assert_called_once()

    async def test_clears_website_when_none(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = UpdatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = UpdatePublisherCommand(
            publisher_id="pub-001", name="Penguin", website=None
        )

        result = await use_case.execute(cmd)

        assert result.website is None

    async def test_raises_publisher_not_found(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=None)
        use_case = UpdatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = UpdatePublisherCommand(
            publisher_id="missing-id", name="Any Name", website=None
        )

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(cmd)

    async def test_idempotent_update_with_same_values(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = UpdatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = UpdatePublisherCommand(
            publisher_id="pub-001",
            name="Penguin Random House",
            website="https://penguinrandomhouse.com",
        )

        result = await use_case.execute(cmd)

        assert result.name == "Penguin Random House"
        assert result.website == "https://penguinrandomhouse.com"
        db_session.commit.assert_called_once()
