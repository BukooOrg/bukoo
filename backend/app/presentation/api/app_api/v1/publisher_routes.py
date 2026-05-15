from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.publisher_dto import (
    CreatePublisherCommand,
    SoftDeletePublisherCommand,
    UpdatePublisherCommand,
)
from app.application.use_cases.publisher import (
    CreatePublisherUseCase,
    SoftDeletePublisherUseCase,
    UpdatePublisherUseCase,
)
from app.presentation.dependencies.deps import AdminUser, DbSession, PublisherRepo
from app.presentation.schemas.publisher_schema import (
    CreatePublisherRequest,
    CreatePublisherResponse,
    SoftDeletePublisherResponse,
    UpdatePublisherRequest,
    UpdatePublisherResponse,
)

router = APIRouter(prefix="/publishers", tags=["publisher"])


@router.post(
    "",
    status_code=201,
    response_model=CreatePublisherResponse,
    operation_id="createPublisher",
)
async def create_publisher(
    body: CreatePublisherRequest,
    _admin: AdminUser,
    publisher_repo: PublisherRepo,
    db_session: DbSession,
) -> CreatePublisherResponse:
    use_case = CreatePublisherUseCase(
        db_session=db_session, publisher_repo=publisher_repo
    )
    result = await use_case.execute(
        CreatePublisherCommand(name=body.name, website=body.website)
    )
    return CreatePublisherResponse(
        id=result.id,
        name=result.name,
        website=result.website,
        created_at=result.created_at,
    )


@router.patch(
    "/{publisher_id}",
    response_model=UpdatePublisherResponse,
    operation_id="updatePublisher",
)
async def update_publisher(
    publisher_id: str,
    body: UpdatePublisherRequest,
    _admin: AdminUser,
    publisher_repo: PublisherRepo,
    db_session: DbSession,
) -> UpdatePublisherResponse:
    use_case = UpdatePublisherUseCase(
        db_session=db_session, publisher_repo=publisher_repo
    )
    result = await use_case.execute(
        UpdatePublisherCommand(
            publisher_id=publisher_id, name=body.name, website=body.website
        )
    )
    return UpdatePublisherResponse(
        id=result.id,
        name=result.name,
        website=result.website,
        created_at=result.created_at,
    )


@router.delete(
    "/{publisher_id}",
    response_model=SoftDeletePublisherResponse,
    operation_id="softDeletePublisher",
)
async def soft_delete_publisher(
    publisher_id: str,
    _admin: AdminUser,
    publisher_repo: PublisherRepo,
    db_session: DbSession,
) -> SoftDeletePublisherResponse:
    use_case = SoftDeletePublisherUseCase(
        db_session=db_session, publisher_repo=publisher_repo
    )
    result = await use_case.execute(
        SoftDeletePublisherCommand(publisher_id=publisher_id)
    )
    return SoftDeletePublisherResponse(message=result.message)
