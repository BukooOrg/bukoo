from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import (
    ViewCategoryDetailCommand,
    ViewCategoryDetailResult,
)
from app.application.use_cases.category.view_category_detail import (
    ViewCategoryDetailUseCase,
)
from app.domain.entities.category_entity import CategoryEntity
from app.domain.exceptions.category import CategoryNotFoundError
from app.domain.repositories.category_repository import ICategoryRepository


def _make_category(category_id: str = "cat-001") -> CategoryEntity:
    now = datetime.now(UTC)
    return CategoryEntity(
        _id=category_id,
        _collection_id="col-001",
        _name="Science Fiction",
        _url_slug="science-fiction",
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, category: CategoryEntity | None = None) -> None:
        self._category = category

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        if self._category and self._category.id == category_id:
            return self._category
        return None

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        return None

    async def find_all(self, collection: str | None = None) -> list[CategoryEntity]:
        return []

    async def save(self, category: CategoryEntity) -> None:
        pass


@pytest.mark.unit
class TestViewCategoryDetailUseCase:
    async def test_returns_result_with_correct_fields(self) -> None:
        category = _make_category("cat-001")
        repo = FakeCategoryRepository(category=category)
        use_case = ViewCategoryDetailUseCase(db_session=AsyncMock(), category_repo=repo)

        result = await use_case.execute(
            ViewCategoryDetailCommand(category_id="cat-001")
        )

        assert isinstance(result, ViewCategoryDetailResult)
        assert result.id == "cat-001"
        assert result.collection_id == "col-001"
        assert result.name == "Science Fiction"
        assert result.url_slug == "science-fiction"
        assert isinstance(result.created_at, datetime)

    async def test_raises_not_found_when_repo_returns_none(self) -> None:
        repo = FakeCategoryRepository(category=None)
        use_case = ViewCategoryDetailUseCase(db_session=AsyncMock(), category_repo=repo)

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(
                ViewCategoryDetailCommand(category_id="nonexistent-id")
            )

    async def test_raises_not_found_for_soft_deleted_category(self) -> None:
        deleted_category = _make_category("cat-001")
        deleted_category._deleted_at = datetime.now(UTC)
        repo = FakeCategoryRepository(category=None)
        use_case = ViewCategoryDetailUseCase(db_session=AsyncMock(), category_repo=repo)

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(ViewCategoryDetailCommand(category_id="cat-001"))

    async def test_raises_not_found_when_id_does_not_match(self) -> None:
        category = _make_category("cat-001")
        repo = FakeCategoryRepository(category=category)
        use_case = ViewCategoryDetailUseCase(db_session=AsyncMock(), category_repo=repo)

        with pytest.raises(CategoryNotFoundError):
            await use_case.execute(ViewCategoryDetailCommand(category_id="cat-999"))
