"""User profile routes — self-service account management."""

from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.user_dto import UpdateProfileCommand
from app.application.use_cases.user.update_profile import UpdateProfileUseCase
from app.core.util import build_public_url
from app.presentation.dependencies.deps import CurrentUser, DbSession, UserRepo
from app.presentation.schemas.user_schema import (
    UpdateProfileRequest,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse, operation_id="getMe")
async def get_me(current_user: CurrentUser) -> UserProfileResponse:
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        date_of_birth=current_user.date_of_birth,
        role=current_user.role,
        status=current_user.status,
        avatar_url=build_public_url(current_user.avatar_url),
        have_password=current_user.have_password,
        last_login_at=current_user.last_login_at,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
    )


@router.patch("/me", response_model=UserProfileResponse, operation_id="updateProfile")
async def update_profile(
    body: UpdateProfileRequest,
    current_user: CurrentUser,
    user_repo: UserRepo,
    db_session: DbSession,
) -> UserProfileResponse:
    use_case = UpdateProfileUseCase(db_session=db_session, user_repo=user_repo)
    result = await use_case.execute(
        UpdateProfileCommand(
            user_id=current_user.id,
            full_name=body.full_name,
            date_of_birth=body.date_of_birth,
        )
    )
    return UserProfileResponse(
        id=result.id,
        email=result.email,
        full_name=result.full_name,
        date_of_birth=result.date_of_birth,
        role=result.role,
        status=result.status,
        avatar_url=build_public_url(result.avatar_url),
        have_password=result.have_password,
        last_login_at=result.last_login_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
