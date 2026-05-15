from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.dtos.publisher_dto import (
    CreatePublisherCommand,
    CreatePublisherResult,
)
from app.application.use_cases.publisher.create_publisher import CreatePublisherUseCase
from app.domain.entities import PublisherEntity
from app.domain.repositories.publisher_repository import IPublisherRepository


class FakePublisherRepository(IPublisherRepository):
    def __init__(self) -> None:
        self._saved: PublisherEntity | None = None

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        return None

    async def save(self, publisher: PublisherEntity) -> None:
        self._saved = publisher


@pytest.mark.unit
class TestCreatePublisherUseCase:
    async def test_creates_publisher_with_website(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository()
        use_case = CreatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = CreatePublisherCommand(name="Penguin", website="https://example.com")

        result = await use_case.execute(cmd)

        assert isinstance(result, CreatePublisherResult)
        assert result.name == "Penguin"
        assert result.website == "https://example.com"
        assert isinstance(result.id, str) and len(result.id) > 0
        db_session.commit.assert_called_once()

    async def test_creates_publisher_without_website(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository()
        use_case = CreatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = CreatePublisherCommand(name="Penguin", website=None)

        result = await use_case.execute(cmd)

        assert result.name == "Penguin"
        assert result.website is None
        assert len(result.id) > 0

    async def test_use_case_receives_clean_name(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository()
        use_case = CreatePublisherUseCase(db_session=db_session, publisher_repo=repo)
        cmd = CreatePublisherCommand(name="Penguin", website=None)

        result = await use_case.execute(cmd)

        assert repo._saved is not None
        assert repo._saved.name == "Penguin"
        assert result.name == "Penguin"

    async def test_successive_calls_produce_distinct_ids(self) -> None:
        db_session = AsyncMock()
        use_case = CreatePublisherUseCase(
            db_session=db_session, publisher_repo=FakePublisherRepository()
        )
        cmd = CreatePublisherCommand(name="HarperCollins", website=None)

        result_1 = await use_case.execute(cmd)
        result_2 = await use_case.execute(cmd)

        assert result_1.id != result_2.id
