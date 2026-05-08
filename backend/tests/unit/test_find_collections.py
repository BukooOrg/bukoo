from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import BaseCategoryResult
from app.application.dtos.collection_dto import (
    BaseCollectionResult,
    FindCollectionsResult,
)
from app.application.use_cases.collection.find_collections import FindCollectionsUseCase
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.collection_entity import CollectionEntity
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


def _make_collection(
    name: str = "Fiction", with_category: bool = False
) -> CollectionEntity:
    now = _now()
    collection = CollectionEntity(
        _id="col-id-1",
        _name=name,
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )
    if with_category:
        collection._categories.append(_make_category(collection_id=collection.id))
    return collection


class FakeCollectionRepository(ICollectionRepository):
    def __init__(self, collections: list[CollectionEntity] | None = None) -> None:
        self._collections = collections or []

    async def find_all(self) -> list[CollectionEntity]:
        return self._collections

    async def find_by_url_slug(self, url_slug: str) -> CollectionEntity | None:
        return next((c for c in self._collections if c.url_slug == url_slug), None)

    async def save(self, collection: CollectionEntity) -> None:
        self._collections.append(collection)


@pytest.mark.unit
class TestFindCollectionsUseCase:
    async def test_returns_all_collections(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository(
            collections=[_make_collection("Fiction"), _make_collection("Non-Fiction")]
        )
        use_case = FindCollectionsUseCase(db_session=db_session, collection_repo=repo)

        result = await use_case.execute()

        assert isinstance(result, FindCollectionsResult)
        assert len(result.collections) == 2
        assert all(isinstance(c, BaseCollectionResult) for c in result.collections)

    async def test_maps_categories_correctly(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository(
            collections=[_make_collection(with_category=True)]
        )
        use_case = FindCollectionsUseCase(db_session=db_session, collection_repo=repo)

        result = await use_case.execute()

        collection = result.collections[0]
        assert len(collection.categories) == 1
        cat = collection.categories[0]
        assert isinstance(cat, BaseCategoryResult)
        assert cat.id == "cat-id-1"
        assert cat.collection_id == "col-id-1"
        assert cat.name == "Literary Fiction"
        assert cat.url_slug == "literary-fiction"
        assert isinstance(cat.created_at, datetime)

    async def test_returns_empty_list_when_no_collections(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository(collections=[])
        use_case = FindCollectionsUseCase(db_session=db_session, collection_repo=repo)

        result = await use_case.execute()

        assert result.collections == []

    async def test_collection_with_no_categories_has_empty_list(self) -> None:
        db_session = AsyncMock()
        repo = FakeCollectionRepository(
            collections=[_make_collection(with_category=False)]
        )
        use_case = FindCollectionsUseCase(db_session=db_session, collection_repo=repo)

        result = await use_case.execute()

        assert result.collections[0].categories == []
