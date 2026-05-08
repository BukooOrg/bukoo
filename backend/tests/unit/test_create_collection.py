from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.application.dtos.collection_dto import (
    CreateCollectionCommand,
    CreateCollectionResult,
)
from app.application.use_cases.collection.create_collection import (
    CreateCollectionUseCase,
)
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.collection import CollectionAlreadyExistsError
from app.domain.repositories.collection_repository import ICollectionRepository


def _make_collection(url_slug: str = "fiction") -> CollectionEntity:
    from datetime import UTC, datetime

    now = datetime.now(UTC)
    return CollectionEntity(
        _id="test-id",
        _name="Fiction",
        _url_slug=url_slug,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCollectionRepository(ICollectionRepository):
    def __init__(self, existing: CollectionEntity | None = None) -> None:
        self._existing = existing
        self._saved: CollectionEntity | None = None
        self._collections = []

    async def find_all(self) -> list[CollectionEntity]:
        return self._collections

    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        if self._existing and self._existing.url_slug == url_slug:
            return self._existing
        return None

    async def save(self, collection: CollectionEntity) -> None:
        self._saved = collection
        self._collections.append(collection)


@pytest.mark.unit
class TestCreateCollectionUseCase:
    async def test_creates_collection_successfully(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository()
        use_case = CreateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = CreateCollectionCommand(
            name="Science & Technology", url_slug="science-and-technology"
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateCollectionResult)
        assert result.name == "Science & Technology"
        assert result.url_slug == "science-and-technology"
        assert result.categories == []
        db_session.commit.assert_called_once()

    async def test_result_id_is_non_empty_string(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository()
        use_case = CreateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = CreateCollectionCommand(name="Fiction", url_slug="fiction")

        result = await use_case.execute(cmd)

        assert isinstance(result.id, str)
        assert len(result.id) > 0

    async def test_raises_when_slug_already_exists(self) -> None:
        db_session = AsyncMock()
        existing = _make_collection(url_slug="fiction")
        repo = FakeCollectionRepository(existing=existing)
        use_case = CreateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = CreateCollectionCommand(name="Another Fiction", url_slug="fiction")

        with pytest.raises(CollectionAlreadyExistsError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_categories_is_empty_list_on_creation(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository()
        use_case = CreateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = CreateCollectionCommand(name="Non-Fiction", url_slug="non-fiction")

        result = await use_case.execute(cmd)

        assert result.categories == []
