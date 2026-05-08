from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.collection_dto import (
    UpdateCollectionCommand,
    UpdateCollectionResult,
)
from app.application.use_cases.collection.update_collection import (
    UpdateCollectionUseCase,
)
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.collection import (
    CollectionAlreadyExistsError,
    CollectionNotFoundError,
)
from app.domain.repositories.collection_repository import ICollectionRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _make_collection(
    collection_id: str = "col-id-1",
    name: str = "Fiction",
    url_slug: str = "fiction",
) -> CollectionEntity:
    now = _now()
    return CollectionEntity(
        _id=collection_id,
        _name=name,
        _url_slug=url_slug,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCollectionRepository(ICollectionRepository):
    def __init__(self, *collections: CollectionEntity) -> None:
        self._by_id = {c.id: c for c in collections}
        self._by_slug = {c.url_slug: c for c in collections}
        self._saved: CollectionEntity | None = None

    async def find_by_id(self, collection_id: str) -> CollectionEntity | None:
        return self._by_id.get(collection_id)

    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        return self._by_slug.get(url_slug)

    async def find_all(self) -> list[CollectionEntity]:
        return list(self._by_id.values())

    async def save(self, collection: CollectionEntity) -> None:
        self._saved = collection
        self._by_id[collection.id] = collection
        self._by_slug[collection.url_slug] = collection

    async def soft_delete_with_categories(self, collection_id: str) -> None:
        pass


@pytest.mark.unit
class TestUpdateCollectionUseCase:
    async def test_updates_name_and_slug_successfully(self) -> None:
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        use_case = UpdateCollectionUseCase(db_session=AsyncMock(), collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="col-id-1",
            name="Updated Fiction",
            url_slug="updated-fiction",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateCollectionResult)
        assert result.name == "Updated Fiction"
        assert result.url_slug == "updated-fiction"
        assert result.id == "col-id-1"

    async def test_commit_is_called_on_success(self) -> None:
        collection = _make_collection()
        repo = FakeCollectionRepository(collection)
        db_session = AsyncMock()
        use_case = UpdateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="col-id-1", name="New Name", url_slug="new-slug"
        )

        await use_case.execute(cmd)

        db_session.commit.assert_called_once()

    async def test_updating_same_slug_does_not_raise(self) -> None:
        collection = _make_collection(url_slug="fiction")
        repo = FakeCollectionRepository(collection)
        use_case = UpdateCollectionUseCase(db_session=AsyncMock(), collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="col-id-1", name="Fiction Updated", url_slug="fiction"
        )

        result = await use_case.execute(cmd)

        assert result.url_slug == "fiction"
        assert result.name == "Fiction Updated"

    async def test_raises_not_found_when_collection_missing(self) -> None:
        repo = FakeCollectionRepository()
        use_case = UpdateCollectionUseCase(db_session=AsyncMock(), collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="nonexistent-id", name="Fiction", url_slug="fiction"
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(cmd)

    async def test_raises_conflict_when_slug_belongs_to_another_collection(
        self,
    ) -> None:
        target = _make_collection(collection_id="col-id-1", url_slug="fiction")
        other = _make_collection(
            collection_id="col-id-2", name="Non-Fiction", url_slug="non-fiction"
        )
        repo = FakeCollectionRepository(target, other)
        use_case = UpdateCollectionUseCase(db_session=AsyncMock(), collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="col-id-1", name="Fiction", url_slug="non-fiction"
        )

        with pytest.raises(CollectionAlreadyExistsError):
            await use_case.execute(cmd)

    async def test_commit_not_called_when_collection_not_found(self) -> None:
        repo = FakeCollectionRepository()
        db_session = AsyncMock()
        use_case = UpdateCollectionUseCase(db_session=db_session, collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="ghost-id", name="Ghost", url_slug="ghost"
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_same_slug_does_not_trigger_uniqueness_check(self) -> None:
        same_url_slug = "fiction"
        collection = _make_collection(collection_id="col-id-1", url_slug=same_url_slug)
        other = _make_collection(
            collection_id="col-id-2", name="Non-Fiction", url_slug="non-fiction"
        )
        repo = FakeCollectionRepository(collection, other)
        use_case = UpdateCollectionUseCase(db_session=AsyncMock(), collection_repo=repo)
        cmd = UpdateCollectionCommand(
            collection_id="col-id-1", name="Fiction Renamed", url_slug=same_url_slug
        )

        result = await use_case.execute(cmd)

        assert result.name == "Fiction Renamed"
        assert result.url_slug == same_url_slug
