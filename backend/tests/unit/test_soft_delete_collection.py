from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.collection_dto import (
    SoftDeleteCollectionCommand,
    SoftDeleteCollectionResult,
)
from app.application.use_cases.collection.soft_delete_collection import (
    SoftDeleteCollectionUseCase,
)
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.collection import CollectionNotFoundError
from app.domain.repositories.collection_repository import ICollectionRepository


def _make_collection(collection_id: str = "col-id-1") -> CollectionEntity:
    now = datetime.now(UTC)
    return CollectionEntity(
        _id=collection_id,
        _name="Fiction",
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCollectionRepository(ICollectionRepository):
    def __init__(self, *collections: CollectionEntity) -> None:
        self._by_id = {c.id: c for c in collections}
        self._saved: CollectionEntity | None = None
        self.soft_delete_called_with: str | None = None

    async def find_by_id(self, collection_id: str) -> CollectionEntity | None:
        return self._by_id.get(collection_id)

    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        return None

    async def find_all(self) -> list[CollectionEntity]:
        return list(self._by_id.values())

    async def save(self, collection: CollectionEntity) -> None:
        self._saved = collection

    async def soft_delete_with_categories(self, collection_id: str) -> None:
        self.soft_delete_called_with = collection_id


@pytest.mark.unit
class TestSoftDeleteCollectionUseCase:
    async def test_returns_success_result(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id=collection.id)

        result = await use_case.execute(command)

        assert isinstance(result, SoftDeleteCollectionResult)
        assert result.message == "Collection deleted successfully."

    async def test_entity_deleted_at_is_set(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id=collection.id)

        await use_case.execute(command)

        assert repo._saved is not None
        assert repo._saved.deleted_at is not None

    async def test_soft_delete_with_categories_called(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id=collection.id)

        await use_case.execute(command)

        assert repo.soft_delete_called_with == collection.id

    async def test_save_called(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id=collection.id)

        await use_case.execute(command)

        assert repo._saved is not None

    async def test_db_session_commit_called(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id=collection.id)

        await use_case.execute(command)

        db_session.commit.assert_called_once()

    async def test_raises_collection_not_found_when_missing(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository()
        use_case = SoftDeleteCollectionUseCase(
            db_session=db_session, collection_repo=repo
        )
        command = SoftDeleteCollectionCommand(collection_id="nonexistent-id")

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(command)
