"""User profile routes — self-service account management."""

from __future__ import annotations

from fastapi import APIRouter, Response, UploadFile

from app.application.dtos.user_dto import (
    GetMyAddressCommand,
    RemoveAvatarCommand,
    SoftDeleteMeCommand,
    UpdateAvatarCommand,
    UpdateProfileCommand,
    UpsertAddressCommand,
)
from app.application.use_cases.user.get_my_address import GetMyAddressUseCase
from app.application.use_cases.user.remove_avatar import RemoveAvatarUseCase
from app.application.use_cases.user.soft_delete_me import SoftDeleteMeUseCase
from app.application.use_cases.user.update_avatar import UpdateAvatarUseCase
from app.application.use_cases.user.update_profile import UpdateProfileUseCase
from app.application.use_cases.user.upsert_address import UpsertAddressUseCase
from app.core.constants import ALLOWED_AVATAR_TYPES, MAX_AVATAR_BYTES
from app.core.util import build_public_url, clear_auth_cookie
from app.domain.exceptions import FileSizeExceededError, InvalidFileTypeError
from app.presentation.dependencies.deps import (
    AddressRepo,
    CurrentUser,
    CustomerUser,
    DbSession,
    StorageService,
    TokenPayload,
    TokenService,
    UserRepo,
)
from app.presentation.schemas.user_schema import (
    AddressResponse,
    SoftDeleteMeResponse,
    UpdateProfileRequest,
    UpsertAddressRequest,
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


@router.delete("/me", response_model=SoftDeleteMeResponse, operation_id="softDeleteMe")
async def soft_delete_me(
    current_user: CurrentUser,
    token_payload: TokenPayload,
    token_svc: TokenService,
    user_repo: UserRepo,
    db_session: DbSession,
    response: Response,
) -> SoftDeleteMeResponse:
    use_case = SoftDeleteMeUseCase(
        db_session=db_session, user_repo=user_repo, token_svc=token_svc
    )
    result = await use_case.execute(
        SoftDeleteMeCommand(user_id=current_user.id, token_payload=token_payload)
    )
    clear_auth_cookie(response)
    return SoftDeleteMeResponse(message=result.message)


@router.post(
    "/me/avatar", response_model=UserProfileResponse, operation_id="updateAvatar"
)
async def update_avatar(
    file: UploadFile,
    current_user: CurrentUser,
    user_repo: UserRepo,
    storage_svc: StorageService,
    db_session: DbSession,
) -> UserProfileResponse:
    if file.content_type not in ALLOWED_AVATAR_TYPES:
        raise InvalidFileTypeError(ALLOWED_AVATAR_TYPES)

    file_data = await file.read()
    if len(file_data) > MAX_AVATAR_BYTES:
        raise FileSizeExceededError(MAX_AVATAR_BYTES // 1024**2, "MB")

    content_type = file.content_type or "application/octet-stream"
    use_case = UpdateAvatarUseCase(
        db_session=db_session,
        user_repo=user_repo,
        storage_svc=storage_svc,
    )
    result = await use_case.execute(
        UpdateAvatarCommand(
            user_id=current_user.id,
            file_data=file_data,
            content_type=content_type,
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


@router.delete(
    "/me/avatar", response_model=UserProfileResponse, operation_id="removeAvatar"
)
async def remove_avatar(
    current_user: CurrentUser,
    user_repo: UserRepo,
    storage_svc: StorageService,
    db_session: DbSession,
) -> UserProfileResponse:
    use_case = RemoveAvatarUseCase(
        db_session=db_session, user_repo=user_repo, storage_svc=storage_svc
    )
    result = await use_case.execute(RemoveAvatarCommand(user_id=current_user.id))
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


@router.get("/me/address", response_model=AddressResponse, operation_id="getMyAddress")
async def get_my_address(
    current_user: CustomerUser, user_repo: UserRepo, db_session: DbSession
) -> AddressResponse:
    use_case = GetMyAddressUseCase(db_session=db_session, user_repo=user_repo)
    result = await use_case.execute(GetMyAddressCommand(current_user.id))
    return AddressResponse(
        id=result.id,
        user_id=result.user_id,
        recipient_name=result.recipient_name,
        phone=result.phone,
        address_line1=result.address_line1,
        address_line2=result.address_line2,
        city=result.city,
        state=result.state,
        postcode=result.postcode,
        country=result.country,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.put("/me/address", response_model=AddressResponse, operation_id="upsertAddress")
async def upsert_address(
    body: UpsertAddressRequest,
    current_user: CustomerUser,
    user_repo: UserRepo,
    address_repo: AddressRepo,
    db_session: DbSession,
) -> AddressResponse:
    use_case = UpsertAddressUseCase(
        db_session=db_session,
        user_repo=user_repo,
        address_repo=address_repo,
    )
    result = await use_case.execute(
        UpsertAddressCommand(
            user_id=current_user.id,
            recipient_name=body.recipient_name,
            phone=body.phone,
            address_line1=body.address_line1,
            address_line2=body.address_line2,
            city=body.city,
            state=body.state,
            postcode=body.postcode,
            country=body.country,
        )
    )
    return AddressResponse(
        id=result.id,
        user_id=result.user_id,
        recipient_name=result.recipient_name,
        phone=result.phone,
        address_line1=result.address_line1,
        address_line2=result.address_line2,
        city=result.city,
        state=result.state,
        postcode=result.postcode,
        country=result.country,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )
