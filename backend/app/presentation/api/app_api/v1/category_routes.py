"""Category management route"""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.category_dto import CreateCategoryCommand
from app.application.use_cases.category import CreateCategoryUseCase
from app.presentation.dependencies.deps import (
    AdminUser,
    CategoryRepo,
    CollectionRepo,
    DbSession,
)
from app.presentation.schemas.category_schema import (
    CreateCategoryRequest,
    CreateCategoryResponse,
)

router = APIRouter(prefix="/categories", tags=["category"])


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
