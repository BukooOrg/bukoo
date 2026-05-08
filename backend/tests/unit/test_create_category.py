from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import (
    CreateCategoryCommand,
    CreateCategoryResult,
)
from app.application.use_cases.category.create_category import CreateCategoryUseCase
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.category import CategoryAlreadyExistsError
from app.domain.exceptions.collection import CollectionNotFoundError
from app.domain.repositories.category_repository import ICategoryRepository
from app.domain.repositories.collection_repository import ICollectionRepository


def _make_collection(collection_id: str = "col-001") -> CollectionEntity:
    now = datetime.now(UTC)
    return CollectionEntity(
        _id=collection_id,
        _name="Fiction",
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
        _categories=[],
    )


def _make_category(url_slug: str = "science-fiction") -> CategoryEntity:
    now = datetime.now(UTC)
    return CategoryEntity(
        _id="cat-001",
        _collection_id="col-001",
        _name="Science Fiction",
        _url_slug=url_slug,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


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


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, existing: CategoryEntity | None = None) -> None:
        self._existing = existing
        self._saved: CategoryEntity | None = None

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        return None

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        if self._existing and self._existing.url_slug == url_slug:
            return self._existing
        return None

    async def find_all(self, collection: str | None = None) -> list[CategoryEntity]:
        return []

    async def save(self, category: CategoryEntity) -> None:
        self._saved = category


@pytest.mark.unit
class TestCreateCategoryUseCase:
    async def test_creates_category_successfully(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection("col-001")
        collection_repo = FakeCollectionRepository(collection=collection)
        category_repo = FakeCategoryRepository()
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="col-001",
            name="Science Fiction",
            url_slug="science-fiction",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, CreateCategoryResult)
        assert result.collection_id == "col-001"
        assert result.name == "Science Fiction"
        assert result.url_slug == "science-fiction"
        assert isinstance(result.id, str) and len(result.id) > 0
        db_session.commit.assert_called_once()

    async def test_result_id_is_non_empty_string(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection("col-001")
        collection_repo = FakeCollectionRepository(collection=collection)
        category_repo = FakeCategoryRepository()
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="col-001", name="Horror", url_slug="horror"
        )

        result = await use_case.execute(cmd)

        assert len(result.id) > 0

    async def test_raises_when_collection_not_found(self) -> None:
        db_session = AsyncMock()
        collection_repo = FakeCollectionRepository(collection=None)
        category_repo = FakeCategoryRepository()
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="nonexistent-col",
            name="Science Fiction",
            url_slug="science-fiction",
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_raises_when_url_slug_already_exists(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection("col-001")
        collection_repo = FakeCollectionRepository(collection=collection)
        existing_category = _make_category(url_slug="science-fiction")
        category_repo = FakeCategoryRepository(existing=existing_category)
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="col-001",
            name="Different Name",
            url_slug="science-fiction",
        )

        with pytest.raises(CategoryAlreadyExistsError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_save_not_called_when_collection_missing(self) -> None:
        db_session = AsyncMock()
        collection_repo = FakeCollectionRepository(collection=None)
        category_repo = FakeCategoryRepository()
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="nonexistent-col",
            name="Science Fiction",
            url_slug="science-fiction",
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(cmd)

        assert category_repo._saved is None

    async def test_save_not_called_when_slug_conflict(self) -> None:
        db_session = AsyncMock()
        collection = _make_collection("col-001")
        collection_repo = FakeCollectionRepository(collection=collection)
        existing_category = _make_category(url_slug="science-fiction")
        category_repo = FakeCategoryRepository(existing=existing_category)
        use_case = CreateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = CreateCategoryCommand(
            collection_id="col-001",
            name="Different Name",
            url_slug="science-fiction",
        )

        with pytest.raises(CategoryAlreadyExistsError):
            await use_case.execute(cmd)

        assert category_repo._saved is None
