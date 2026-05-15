from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.publisher_dto import CreatePublisherCommand
from app.application.use_cases.publisher import CreatePublisherUseCase
from app.presentation.dependencies.deps import AdminUser, DbSession, PublisherRepo
from app.presentation.schemas.publisher_schema import (
    CreatePublisherRequest,
    CreatePublisherResponse,
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
