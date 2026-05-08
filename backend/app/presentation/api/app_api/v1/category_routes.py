"""Category management route"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.application.dtos.category_dto import (
    CreateCategoryCommand,
    FindCategoriesCommand,
    ViewCategoryDetailCommand,
)
from app.application.use_cases.category import (
    CreateCategoryUseCase,
    FindCategoriesUseCase,
    ViewCategoryDetailUseCase,
)
from app.presentation.dependencies.deps import (
    AdminUser,
    CategoryRepo,
    CollectionRepo,
    DbSession,
)
from app.presentation.schemas.category_schema import (
    CategoryListResponse,
    CreateCategoryRequest,
    CreateCategoryResponse,
    ViewCategoryDetailResponse,
)

router = APIRouter(prefix="/categories", tags=["category"])


@router.get(
    "",
    response_model=list[CategoryListResponse],
    operation_id="findCategories",
)
async def find_categories(
    category_repo: CategoryRepo,
    db_session: DbSession,
    collection_id: UUID | None = None,
) -> list[CategoryListResponse]:
    use_case = FindCategoriesUseCase(db_session=db_session, category_repo=category_repo)
    result = await use_case.execute(
        FindCategoriesCommand(
            collection_id=str(collection_id) if collection_id else None
        )
    )
    return [
        CategoryListResponse(
            id=c.id,
            collection_id=c.collection_id,
            name=c.name,
            url_slug=c.url_slug,
            created_at=c.created_at,
        )
        for c in result.categories
    ]


@router.get(
    "/{category_id}",
    response_model=ViewCategoryDetailResponse,
    operation_id="viewCategoryDetail",
)
async def view_category_detail(
    category_id: str, category_repo: CategoryRepo, db_session: DbSession
) -> ViewCategoryDetailResponse:
    use_case = ViewCategoryDetailUseCase(
        db_session=db_session, category_repo=category_repo
    )
    result = await use_case.execute(ViewCategoryDetailCommand(category_id=category_id))
    return ViewCategoryDetailResponse(
        id=result.id,
        collection_id=result.collection_id,
        name=result.name,
        url_slug=result.url_slug,
        created_at=result.created_at,
    )


@router.post(
    "",
    response_model=CreateCategoryResponse,
    status_code=201,
    operation_id="createCategory",
)
async def create_category(
    body: CreateCategoryRequest,
    _admin: AdminUser,
    collection_repo: CollectionRepo,
    category_repo: CategoryRepo,
    db_session: DbSession,
) -> CreateCategoryResponse:
    use_case = CreateCategoryUseCase(
        db_session=db_session,
        category_repo=category_repo,
        collection_repo=collection_repo,
    )
    result = await use_case.execute(
        CreateCategoryCommand(
            collection_id=body.collection_id, name=body.name, url_slug=body.url_slug
        )
    )
    return CreateCategoryResponse(
        id=result.id,
        collection_id=result.collection_id,
        name=result.name,
        url_slug=result.url_slug,
        created_at=result.created_at,
    )
