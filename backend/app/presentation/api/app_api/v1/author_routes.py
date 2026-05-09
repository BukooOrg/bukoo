from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.author_dto import (
    CreateAuthorCommand,
)
from app.application.use_cases.author import CreateAuthorUseCase
from app.presentation.dependencies.deps import AdminUser, AuthorRepo, DbSession
from app.presentation.schemas.author_schema import (
    CreateAuthorRequest,
    CreateAuthorResponse,
)

router = APIRouter(prefix="/authors", tags=["author"])


@router.post(
    "",
    status_code=201,
    response_model=CreateAuthorResponse,
    operation_id="createAuthor",
)
async def create_author(
    body: CreateAuthorRequest,
    _admin: AdminUser,
    author_repo: AuthorRepo,
    db_session: DbSession,
) -> CreateAuthorResponse:
    use_case = CreateAuthorUseCase(db_session=db_session, author_repo=author_repo)
    result = await use_case.execute(CreateAuthorCommand(name=body.name))
    return CreateAuthorResponse(
        id=result.id, name=result.name, created_at=result.created_at
    )
