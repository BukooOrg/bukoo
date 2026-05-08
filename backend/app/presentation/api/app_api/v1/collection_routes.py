"""Collection routes — admin collection management."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.collection_dto import CreateCollectionCommand
from app.application.use_cases.collection.create_collection import (
    CreateCollectionUseCase,
)
from app.application.use_cases.collection.find_collections import FindCollectionsUseCase
from app.presentation.dependencies.deps import AdminUser, CollectionRepo, DbSession
from app.presentation.schemas.category_schema import CategoryResponse
from app.presentation.schemas.collection_schema import (
    CollectionListItemResponse,
    CollectionResponse,
    CreateCollectionRequest,
)

router = APIRouter(prefix="/collections", tags=["collections"])


@router.get(
    "", response_model=list[CollectionListItemResponse], operation_id="findCollections"
)
async def find_collections(
    collection_repo: CollectionRepo,
    db_session: DbSession,
) -> list[CollectionListItemResponse]:
    use_case = FindCollectionsUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute()
    return [
        CollectionListItemResponse(
            id=c.id,
            name=c.name,
            url_slug=c.url_slug,
            created_at=c.created_at,
            categories=[
                CategoryResponse(
                    id=cat.id,
                    collection_id=cat.collection_id,
                    name=cat.name,
                    url_slug=cat.url_slug,
                    created_at=cat.created_at,
                )
                for cat in c.categories
            ],
        )
        for c in result.collections
    ]


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
