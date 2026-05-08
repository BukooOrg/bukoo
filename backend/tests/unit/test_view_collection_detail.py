from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import BaseCategoryResult
from app.application.dtos.collection_dto import (
    ViewCollectionDetailCommand,
    ViewCollectionDetailResult,
)
from app.application.use_cases.collection.view_collection_detail import (
    ViewCollectionDetailUseCase,
)
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.collection import CollectionNotFoundError
from app.domain.repositories.collection_repository import ICollectionRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _make_category(
    collection_id: str, name: str = "Literary Fiction"
) -> CategoryEntity:
    now = _now()
    return CategoryEntity(
        _id="cat-id-1",
        _collection_id=collection_id,
        _name=name,
        _url_slug="literary-fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


def _make_collection(with_category: bool = False) -> CollectionEntity:
    now = _now()
    collection = CollectionEntity(
        _id="col-id-1",
        _name="Fiction",
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )
    if with_category:
        collection._categories.append(_make_category(collection_id=collection.id))
    return collection


class FakeCollectionRepository(ICollectionRepository):
    def __init__(self, collection: CollectionEntity | None = None) -> None:
        self._collection = collection

    async def find_by_id(self, collection_id: str) -> CollectionEntity | None:
        if self._collection and self._collection.id == collection_id:
            return self._collection
        return None

    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        return None

    async def find_all(self) -> list[CollectionEntity]:
        return []

    async def save(self, collection: CollectionEntity) -> None:
        pass

    async def soft_delete_with_categories(self, collection_id: str) -> None:
        pass


@pytest.mark.unit
class TestViewCollectionDetailUseCase:
    async def test_returns_result_with_correct_fields(self) -> None:
        collection = _make_collection(with_category=True)
        repo = FakeCollectionRepository(collection=collection)
        use_case = ViewCollectionDetailUseCase(
            db_session=AsyncMock(), collection_repo=repo
        )

        result = await use_case.execute(
            ViewCollectionDetailCommand(collection_id="col-id-1")
        )

        assert isinstance(result, ViewCollectionDetailResult)
        assert result.id == "col-id-1"
        assert result.name == "Fiction"
        assert result.url_slug == "fiction"
        assert isinstance(result.created_at, datetime)

    async def test_maps_categories_correctly(self) -> None:
        collection = _make_collection(with_category=True)
        repo = FakeCollectionRepository(collection=collection)
        use_case = ViewCollectionDetailUseCase(
            db_session=AsyncMock(), collection_repo=repo
        )

        result = await use_case.execute(
            ViewCollectionDetailCommand(collection_id="col-id-1")
        )

        assert len(result.categories) == 1
        cat = result.categories[0]
        assert isinstance(cat, BaseCategoryResult)
        assert cat.id == "cat-id-1"
        assert cat.collection_id == "col-id-1"
        assert cat.name == "Literary Fiction"
        assert cat.url_slug == "literary-fiction"
        assert isinstance(cat.created_at, datetime)

    async def test_returns_empty_categories_when_collection_has_none(self) -> None:
        collection = _make_collection(with_category=False)
        repo = FakeCollectionRepository(collection=collection)
        use_case = ViewCollectionDetailUseCase(
            db_session=AsyncMock(), collection_repo=repo
        )

        result = await use_case.execute(
            ViewCollectionDetailCommand(collection_id="col-id-1")
        )

        assert result.categories == []

    async def test_raises_not_found_when_repo_returns_none(self) -> None:
        repo = FakeCollectionRepository(collection=None)
        use_case = ViewCollectionDetailUseCase(
            db_session=AsyncMock(), collection_repo=repo
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(
                ViewCollectionDetailCommand(collection_id="nonexistent-id")
            )

    async def test_raises_not_found_for_soft_deleted_collection(self) -> None:
        deleted_collection = _make_collection()
        deleted_collection._deleted_at = _now()
        repo = FakeCollectionRepository(collection=None)
        use_case = ViewCollectionDetailUseCase(
            db_session=AsyncMock(), collection_repo=repo
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(
                ViewCollectionDetailCommand(collection_id="col-id-1")
            )
