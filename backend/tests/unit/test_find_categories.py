from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.category_dto import (
    BaseCategoryResult,
    FindCategoriesCommand,
    FindCategoriesResult,
)
from app.application.use_cases.category.find_categories import FindCategoriesUseCase
from app.domain.entities.category_entity import CategoryEntity
from app.domain.repositories.category_repository import ICategoryRepository


def _now() -> datetime:
    return datetime.now(UTC)


def _make_category(
    collection_id: str = "col-id-1",
    name: str = "Literary Fiction",
    url_slug: str = "literary-fiction",
    cat_id: str = "cat-id-1",
) -> CategoryEntity:
    now = _now()
    return CategoryEntity(
        _id=cat_id,
        _collection_id=collection_id,
        _name=name,
        _url_slug=url_slug,
        _created_at=now,
        _updated_at=now,
        _deleted_at=None,
    )


class FakeCategoryRepository(ICategoryRepository):
    def __init__(self, categories: list[CategoryEntity] | None = None) -> None:
        self._categories = categories or []

    async def find_by_id(self, category_id: str) -> CategoryEntity | None:
        return next((c for c in self._categories if c.id == category_id), None)

    async def find_by_url_slug(self, url_slug: str) -> CategoryEntity | None:
        return next((c for c in self._categories if c.url_slug == url_slug), None)

    async def find_all(self, collection_id: str | None = None) -> list[CategoryEntity]:
        if collection_id is None:
            return self._categories
        return [c for c in self._categories if c.collection_id == collection_id]

    async def save(self, category: CategoryEntity) -> None:
        self._categories.append(category)


@pytest.mark.unit
class TestFindCategoriesUseCase:
    async def test_returns_all_categories_when_no_filter(self) -> None:
        db_session = AsyncMock()
        repo = FakeCategoryRepository(
            categories=[
                _make_category(collection_id="col-1", cat_id="cat-1"),
                _make_category(collection_id="col-2", cat_id="cat-2"),
            ]
        )
        use_case = FindCategoriesUseCase(db_session=db_session, category_repo=repo)

        result = await use_case.execute(FindCategoriesCommand(collection_id=None))

        assert isinstance(result, FindCategoriesResult)
        assert len(result.categories) == 2
        assert all(isinstance(c, BaseCategoryResult) for c in result.categories)

    async def test_filters_by_collection_id(self) -> None:
        db_session = AsyncMock()
        repo = FakeCategoryRepository(
            categories=[
                _make_category(collection_id="col-1", cat_id="cat-1"),
                _make_category(collection_id="col-2", cat_id="cat-2"),
            ]
        )
        use_case = FindCategoriesUseCase(db_session=db_session, category_repo=repo)

        result = await use_case.execute(FindCategoriesCommand(collection_id="col-1"))

        assert len(result.categories) == 1
        assert result.categories[0].collection_id == "col-1"

    async def test_maps_fields_correctly(self) -> None:
        db_session = AsyncMock()
        now = _now()
        cat = CategoryEntity(
            _id="cat-id-1",
            _collection_id="col-id-1",
            _name="Literary Fiction",
            _url_slug="literary-fiction",
            _created_at=now,
            _updated_at=now,
            _deleted_at=None,
        )
        repo = FakeCategoryRepository(categories=[cat])
        use_case = FindCategoriesUseCase(db_session=db_session, category_repo=repo)

        result = await use_case.execute(FindCategoriesCommand())

        item = result.categories[0]
        assert item.id == "cat-id-1"
        assert item.collection_id == "col-id-1"
        assert item.name == "Literary Fiction"
        assert item.url_slug == "literary-fiction"
        assert item.created_at == now

    async def test_returns_empty_list_when_no_categories(self) -> None:
        db_session = AsyncMock()
        repo = FakeCategoryRepository(categories=[])
        use_case = FindCategoriesUseCase(db_session=db_session, category_repo=repo)

        result = await use_case.execute(FindCategoriesCommand())

        assert result.categories == []

    async def test_returns_empty_list_when_no_match_for_collection(self) -> None:
        db_session = AsyncMock()
        repo = FakeCategoryRepository(
            categories=[_make_category(collection_id="col-1")]
        )
        use_case = FindCategoriesUseCase(db_session=db_session, category_repo=repo)

        result = await use_case.execute(FindCategoriesCommand(collection_id="col-999"))

        assert result.categories == []
