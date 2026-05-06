"""User profile routes — self-service account management."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.util import build_public_url
from app.presentation.dependencies.deps import CurrentUser
from app.presentation.schemas.user_schema import UserProfileResponse

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
