"""Collection routes — admin collection management."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.collection_dto import CreateCollectionCommand
from app.application.use_cases.collection.create_collection import (
    CreateCollectionUseCase,
)
from app.presentation.dependencies.deps import AdminUser, CollectionRepo, DbSession
from app.presentation.schemas.collection_schema import (
    CollectionResponse,
    CreateCollectionRequest,
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.post(
    "",
    response_model=CollectionResponse,
    status_code=201,
    operation_id="createCollection",
)
async def create_collection(
    body: CreateCollectionRequest,
    _admin: AdminUser,
    collection_repo: CollectionRepo,
    db_session: DbSession,
) -> CollectionResponse:
    use_case = CreateCollectionUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute(
        CreateCollectionCommand(name=body.name, url_slug=body.url_slug)
    )
    return CollectionResponse(
        id=result.id,
        name=result.name,
        url_slug=result.url_slug,
        categories=result.categories,
        created_at=result.created_at,
    )
