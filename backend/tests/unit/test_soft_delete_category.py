from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import (
    SoftDeleteCategoryCommand,
    SoftDeleteCategoryResult,
)
from app.application.use_cases.category.soft_delete_category import (
    SoftDeleteCategoryUseCase,
)
from app.domain.entities.category_entity import CategoryEntity
from app.domain.exceptions.category import CategoryNotFoundError
from app.domain.repositories.category_repository import ICategoryRepository


def _make_category(category_id: str = "cat-id-1") -> CategoryEntity:
    now = datetime.now(UTC)
    return CategoryEntity(
        _id=category_id,
        _collection_id="col-id-1",
        _name="Fiction",
        _url_slug="fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, *categories: CategoryEntity) -> None:
        self._by_id = {c.id: c for c in categories}
        self._saved: CategoryEntity | None = None
        self.nullify_called_with: str | None = None

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        return self._by_id.get(category_id)

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        return None

    async def find_all(self, collection_id: str | None = None) -> list[CategoryEntity]:
        return list(self._by_id.values())

    async def save(self, category: CategoryEntity) -> None:
        self._saved = category

    async def nullify_book_category(self, category_id: str) -> None:
        self.nullify_called_with = category_id


@pytest.mark.unit
class TestSoftDeleteCategoryUseCase:
    async def test_returns_success_result(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        repo = FakeCategoryRepository(category)
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id=category.id)

        result = await use_case.execute(command)

        assert isinstance(result, SoftDeleteCategoryResult)
        assert result.message == "Category deleted successfully."

    async def test_entity_deleted_at_is_set(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        repo = FakeCategoryRepository(category)
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id=category.id)

        await use_case.execute(command)

        assert repo._saved is not None
        assert repo._saved.deleted_at is not None

    async def test_nullify_book_category_called(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        repo = FakeCategoryRepository(category)
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id=category.id)

        await use_case.execute(command)

        assert repo.nullify_called_with == category.id

    async def test_save_called(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        repo = FakeCategoryRepository(category)
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id=category.id)

        await use_case.execute(command)

        assert repo._saved is not None

    async def test_db_session_commit_called(self) -> None:
        db_session = AsyncMock()
        category = _make_category()
        repo = FakeCategoryRepository(category)
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id=category.id)

        await use_case.execute(command)

        db_session.commit.assert_called_once()

    async def test_raises_category_not_found_when_missing(self) -> None:
        db_session = AsyncMock()
        repo = FakeCategoryRepository()
        use_case = SoftDeleteCategoryUseCase(db_session=db_session, category_repo=repo)
        command = SoftDeleteCategoryCommand(category_id="nonexistent-id")

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(command)
