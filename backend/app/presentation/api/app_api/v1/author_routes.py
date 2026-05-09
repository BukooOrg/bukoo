from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.author_dto import (
    CreateAuthorCommand,
    UpdateAuthorCommand,
    ViewAuthorDetailCommand,
)
from app.application.use_cases.author import (
    CreateAuthorUseCase,
    UpdateAuthorUseCase,
    ViewAuthorDetailUseCase,
)
from app.presentation.dependencies.deps import AdminUser, AuthorRepo, DbSession
from app.presentation.schemas.author_schema import (
    CreateAuthorRequest,
    CreateAuthorResponse,
    UpdateAuthorRequest,
    UpdateAuthorResponse,
    ViewAuthorDetailResponse,
)

router = APIRouter(prefix="/authors", tags=["author"])


@router.get(
    "/{author_id}",
    response_model=ViewAuthorDetailResponse,
    operation_id="viewAuthorDetail",
)
async def view_author_detail(
    author_id: str, author_repo: AuthorRepo, db_session: DbSession
) -> ViewAuthorDetailResponse:
    use_case = ViewAuthorDetailUseCase(db_session=db_session, author_repo=author_repo)
    result = await use_case.execute(ViewAuthorDetailCommand(author_id=author_id))
    return ViewAuthorDetailResponse(
        id=result.id, name=result.name, created_at=result.created_at
    )


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


@router.patch(
    "/{author_id}",
    response_model=UpdateAuthorResponse,
    operation_id="updateAuthor",
)
async def update_author(
    author_id: str,
    body: UpdateAuthorRequest,
    _admin: AdminUser,
    author_repo: AuthorRepo,
    db_session: DbSession,
) -> UpdateAuthorResponse:
    use_case = UpdateAuthorUseCase(db_session=db_session, author_repo=author_repo)
    result = await use_case.execute(
        UpdateAuthorCommand(author_id=author_id, name=body.name)
    )
    return UpdateAuthorResponse(
        id=result.id, name=result.name, created_at=result.created_at
    )
