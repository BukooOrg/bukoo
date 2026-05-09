from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import (
    UpdateCategoryCommand,
    UpdateCategoryResult,
)
from app.application.use_cases.category.update_category import UpdateCategoryUseCase
from app.domain.entities.category_entity import CategoryEntity
from app.domain.entities.collection_entity import CollectionEntity
from app.domain.exceptions.category import (
    CategoryAlreadyExistsError,
    CategoryNotFoundError,
)
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


def _make_category(
    category_id: str = "cat-001",
    collection_id: str = "col-001",
    url_slug: str = "science-fiction",
) -> CategoryEntity:
    now = datetime.now(UTC)
    return CategoryEntity(
        _id=category_id,
        _collection_id=collection_id,
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
    def __init__(
        self,
        target: CategoryEntity | None = None,
        conflicting: CategoryEntity | None = None,
    ) -> None:
        self._target = target
        self._conflicting = conflicting
        self._saved: CategoryEntity | None = None

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        if self._target and self._target.id == category_id:
            return self._target
        return None

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        if self._conflicting and self._conflicting.url_slug == url_slug:
            return self._conflicting
        if self._target and self._target.url_slug == url_slug:
            return self._target
        return None

    async def find_all(self, collection: str | None = None) -> list[CategoryEntity]:
        return []

    async def save(self, category: CategoryEntity) -> None:
        self._saved = category

    async def nullify_book_category(self, category_id: str) -> None:
        pass


@pytest.mark.unit
class TestUpdateCategoryUseCase:
    async def test_updates_category_successfully(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        collection = _make_collection("col-001")
        category_repo = FakeCategoryRepository(target=category)
        collection_repo = FakeCollectionRepository(collection=collection)
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="cat-001",
            collection_id="col-001",
            name="Updated Name",
            url_slug="updated-slug",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateCategoryResult)
        assert result.id == "cat-001"
        assert result.name == "Updated Name"
        assert result.url_slug == "updated-slug"
        assert result.collection_id == "col-001"
        db_session.commit.assert_called_once()

    async def test_raises_when_category_not_found(self) -> None:
        db_session = AsyncMock()
        category_repo = FakeCategoryRepository(target=None)
        collection_repo = FakeCollectionRepository()
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="nonexistent",
            collection_id="col-001",
            name="Name",
            url_slug="slug",
        )

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_raises_when_collection_not_found(self) -> None:
        db_session = AsyncMock()
        category = _make_category(collection_id="col-001")
        category_repo = FakeCategoryRepository(target=category)
        collection_repo = FakeCollectionRepository(collection=None)
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="cat-001",
            collection_id="col-999",
            name="Name",
            url_slug="science-fiction",
        )

        with pytest.raises(CollectionNotFoundError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_raises_when_slug_belongs_to_different_category(self) -> None:
        db_session = AsyncMock()
        category = _make_category(category_id="cat-001", url_slug="old-slug")
        other = _make_category(category_id="cat-002", url_slug="taken-slug")
        category_repo = FakeCategoryRepository(target=category, conflicting=other)
        collection_repo = FakeCollectionRepository(collection=_make_collection())
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="cat-001",
            collection_id="col-001",
            name="Name",
            url_slug="taken-slug",
        )

        with pytest.raises(CategoryAlreadyExistsError):
            await use_case.execute(cmd)

        db_session.commit.assert_not_called()

    async def test_no_collection_lookup_when_collection_id_unchanged(self) -> None:
        db_session = AsyncMock()
        category = _make_category(collection_id="col-001")
        # FakeCollectionRepository returns None for any id — would raise if called
        collection_repo = FakeCollectionRepository(collection=None)
        category_repo = FakeCategoryRepository(target=category)
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="cat-001",
            collection_id="col-001",
            name="New Name",
            url_slug="new-slug",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateCategoryResult)
        db_session.commit.assert_called_once()

    async def test_no_slug_conflict_when_url_slug_unchanged(self) -> None:
        db_session = AsyncMock()
        category = _make_category(url_slug="science-fiction")
        # conflicting set to same category — slug lookup returns self, not a different entity
        category_repo = FakeCategoryRepository(target=category)
        collection_repo = FakeCollectionRepository(collection=_make_collection())
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="cat-001",
            collection_id="col-001",
            name="New Name",
            url_slug="science-fiction",
        )

        result = await use_case.execute(cmd)

        assert isinstance(result, UpdateCategoryResult)
        db_session.commit.assert_called_once()

    async def test_commit_not_called_on_category_not_found(self) -> None:
        db_session = AsyncMock()
        category_repo = FakeCategoryRepository(target=None)
        collection_repo = FakeCollectionRepository()
        use_case = UpdateCategoryUseCase(
            db_session=db_session,
            category_repo=category_repo,
            collection_repo=collection_repo,
        )
        cmd = UpdateCategoryCommand(
            category_id="ghost",
            collection_id="col-001",
            name="Name",
            url_slug="slug",
        )

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(cmd)

        assert category_repo._saved is None
        db_session.commit.assert_not_called()
