from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.publisher_dto import (
    SoftDeletePublisherCommand,
    SoftDeletePublisherResult,
)
from app.application.use_cases.publisher.soft_delete_publisher import (
    SoftDeletePublisherUseCase,
)
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
        _deleted_at=None,
    )


class FakePublisherRepository(IPublisherRepository):
    def __init__(self, publisher: PublisherEntity | None = None) -> None:
        self._publisher: PublisherEntity | None = publisher
        self.saved: PublisherEntity | None = None

    async def find_by_id(self, publisher_id: str) -> PublisherEntity | None:
        if self._publisher and self._publisher.id == publisher_id:
            return self._publisher
        return None

    async def save(self, publisher: PublisherEntity) -> None:
        self.saved = publisher


@pytest.mark.unit
class TestSoftDeletePublisherUseCase:
    async def test_returns_success_message(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="pub-001")

        result = await use_case.execute(cmd)

        assert isinstance(result, SoftDeletePublisherResult)
        assert result.message == "Publisher deleted successfully."

    async def test_soft_delete_sets_deleted_at(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="pub-001")

        await use_case.execute(cmd)

        assert repo.saved is not None
        assert repo.saved.deleted_at is not None

    async def test_save_called_once(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="pub-001")

        await use_case.execute(cmd)

        assert repo.saved is publisher

    async def test_commit_called_once(self) -> None:
        publisher = _make_publisher("pub-001")
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=publisher)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="pub-001")

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    async def test_raises_publisher_not_found(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=None)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="missing-id")

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(cmd)

    async def test_already_deleted_publisher_returns_none_from_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakePublisherRepository(publisher=None)
        use_case = SoftDeletePublisherUseCase(
            db_session=db_session, publisher_repo=repo
        )
        cmd = SoftDeletePublisherCommand(publisher_id="deleted-id")

        with pytest.raises(PublisherNotFoundError):
            await use_case.execute(cmd)
