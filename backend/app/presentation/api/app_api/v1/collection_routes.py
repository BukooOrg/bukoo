"""Collection routes — admin collection management."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.collection_dto import (
    CreateCollectionCommand,
    SoftDeleteCollectionCommand,
    UpdateCollectionCommand,
    ViewCollectionDetailCommand,
)
from app.application.use_cases.collection import (
    CreateCollectionUseCase,
    FindCollectionsUseCase,
    SoftDeleteCollectionUseCase,
    UpdateCollectionUseCase,
    ViewCollectionDetailUseCase,
)
from app.presentation.dependencies.deps import AdminUser, CollectionRepo, DbSession
from app.presentation.schemas.category_schema import BaseCategoryResponse
from app.presentation.schemas.collection_schema import (
    CollectionListItemResponse,
    CreateCollectionRequest,
    CreateCollectionResponse,
    SoftDeleteCollectionResponse,
    UpdateCollectionRequest,
    UpdateCollectionResponse,
    ViewCollectionDetailResponse,
)

router = APIRouter(prefix="/collections", tags=["collection"])


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
                BaseCategoryResponse(
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


@router.get("/{collection_id}", response_model=ViewCollectionDetailResponse)
async def view_collection_detail(
    collection_id: str, collection_repo: CollectionRepo, db_session: DbSession
) -> ViewCollectionDetailResponse:
    use_case = ViewCollectionDetailUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute(
        ViewCollectionDetailCommand(collection_id=collection_id)
    )
    return ViewCollectionDetailResponse(
        id=result.id,
        name=result.name,
        url_slug=result.url_slug,
        categories=[
            BaseCategoryResponse(
                id=cat.id,
                collection_id=cat.collection_id,
                name=cat.name,
                url_slug=cat.url_slug,
                created_at=cat.created_at,
            )
            for cat in result.categories
        ],
        created_at=result.created_at,
    )


@router.post(
    "",
    response_model=CreateCollectionResponse,
    status_code=201,
    operation_id="createCollection",
)
async def create_collection(
    body: CreateCollectionRequest,
    _admin: AdminUser,
    collection_repo: CollectionRepo,
    db_session: DbSession,
) -> CreateCollectionResponse:
    use_case = CreateCollectionUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute(
        CreateCollectionCommand(name=body.name, url_slug=body.url_slug)
    )
    return CreateCollectionResponse(
        id=result.id,
        name=result.name,
        url_slug=result.url_slug,
        categories=[
            BaseCategoryResponse(
                id=cat.id,
                collection_id=cat.collection_id,
                name=cat.name,
                url_slug=cat.url_slug,
                created_at=cat.created_at,
            )
            for cat in result.categories
        ],
        created_at=result.created_at,
    )


@router.patch("/{collection_id}", response_model=UpdateCollectionResponse)
async def update_collection(
    collection_id: str,
    body: UpdateCollectionRequest,
    _admin: AdminUser,
    collection_repo: CollectionRepo,
    db_session: DbSession,
) -> UpdateCollectionResponse:
    use_case = UpdateCollectionUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute(
        UpdateCollectionCommand(
            collection_id=collection_id, name=body.name, url_slug=body.url_slug
        )
    )
    return UpdateCollectionResponse(
        id=result.id,
        name=result.name,
        url_slug=result.url_slug,
        categories=[
            BaseCategoryResponse(
                id=cat.id,
                collection_id=cat.collection_id,
                name=cat.name,
                url_slug=cat.url_slug,
                created_at=cat.created_at,
            )
            for cat in result.categories
        ],
        created_at=result.created_at,
    )


@router.delete(
    "/{collection_id}",
    response_model=SoftDeleteCollectionResponse,
    operation_id="softDeleteCollection",
)
async def soft_delete_collection(
    collection_id: str,
    _admin: AdminUser,
    collection_repo: CollectionRepo,
    db_session: DbSession,
) -> SoftDeleteCollectionResponse:
    use_case = SoftDeleteCollectionUseCase(
        db_session=db_session, collection_repo=collection_repo
    )
    result = await use_case.execute(
        SoftDeleteCollectionCommand(collection_id=collection_id)
    )
    return SoftDeleteCollectionResponse(message=result.message)
