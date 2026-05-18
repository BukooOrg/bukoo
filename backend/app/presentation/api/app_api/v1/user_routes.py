"""User profile routes — self-service account management."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Response, UploadFile

from app.application.dtos.review_dto import (
    SoftDeleteMyReviewCommand,
    UpdateMyReviewCommand,
)
from app.application.dtos.user_dto import (
    ChangePasswordCommand,
    GetMyAddressCommand,
    RegisterAdminCommand,
    RemoveAvatarCommand,
    SoftDeleteMeCommand,
    SuspendUserCommand,
    UpdateAvatarCommand,
    UpdateProfileCommand,
    UpsertAddressCommand,
    ViewUserProfileCommand,
)
from app.application.use_cases.review import (
    FindMyReviewsUseCase,
    SoftDeleteMyReviewUseCase,
    UpdateMyReviewUseCase,
)
from app.application.use_cases.user import (
    ChangePasswordUseCase,
    FindUsersUseCase,
    GetMyAddressUseCase,
    RegisterAdminUseCase,
    RemoveAvatarUseCase,
    SoftDeleteMeUseCase,
    SuspendUserUseCase,
    UpdateAvatarUseCase,
    UpdateProfileUseCase,
    UpsertAddressUseCase,
    ViewUserProfileUseCase,
)
from app.core.constants import ALLOWED_AVATAR_TYPES, MAX_AVATAR_BYTES
from app.core.util import build_public_url, clear_auth_cookie
from app.domain.exceptions import FileSizeExceededError, InvalidFileTypeError
from app.presentation.dependencies.deps import (
    AccountRepo,
    AddressRepo,
    AdminUser,
    CurrentUser,
    CustomerUser,
    DbSession,
    PasswordHasher,
    ReviewRepo,
    StorageService,
    TokenPayload,
    TokenService,
    UserRepo,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta
from app.presentation.schemas.review_schema import (
    BaseReviewBookItem,
    MyReviewListQueryRequest,
    ReviewWithBookItemResponse,
    UpdateMyReviewRequest,
    UpdateMyReviewResponse,
)
from app.presentation.schemas.user_schema import (
    AddressResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    FindUsersQueryRequest,
    RegisterAdminRequest,
    SoftDeleteMeResponse,
    UpdateProfileRequest,
    UpsertAddressRequest,
    UserListItemResponse,
    UserProfileResponse,
)

router = APIRouter(prefix="/users", tags=["user"])


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


@router.patch(
    "/me/password", response_model=ChangePasswordResponse, operation_id="changePassword"
)
async def change_password(
    body: ChangePasswordRequest,
    current_user: CustomerUser,
    user_repo: UserRepo,
    hasher: PasswordHasher,
    db_session: DbSession,
) -> ChangePasswordResponse:
    use_case = ChangePasswordUseCase(
        db_session=db_session, user_repo=user_repo, hasher=hasher
    )
    result = await use_case.execute(
        ChangePasswordCommand(
            user_id=current_user.id,
            current_password=body.current_password,
            new_password=body.new_password,
        )
    )
    return ChangePasswordResponse(message=result.message)


# address
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


# review
@router.get(
    "/me/reviews",
    response_model=PaginatedResponse[ReviewWithBookItemResponse],
    operation_id="findMyReviews",
)
async def find_my_reviews(
    query_params: Annotated[
        MyReviewListQueryRequest, Depends(MyReviewListQueryRequest)
    ],
    customer_user: CustomerUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> PaginatedResponse[ReviewWithBookItemResponse]:
    use_case = FindMyReviewsUseCase(db_session=db_session, review_repo=review_repo)
    result = await use_case.execute(query_params.to_command(customer_user.id))
    return PaginatedResponse(
        items=[
            ReviewWithBookItemResponse(
                id=item.id,
                book_id=item.book_id,
                user_id=item.user_id,
                order_item_id=item.order_item_id,
                rating=item.rating,
                comment=item.comment,
                is_hidden=item.is_hidden,
                hidden_at=item.hidden_at,
                created_at=item.created_at,
                updated_at=item.updated_at,
                book=BaseReviewBookItem(
                    id=item.book.id,
                    title=item.book.title,
                    cover_url=build_public_url(item.book.cover_url),
                ),
            )
            for item in result.items
        ],
        pagination=PaginationMeta.from_result(result),
    )


@router.patch(
    "/me/reviews/{review_id}",
    response_model=UpdateMyReviewResponse,
    operation_id="updateMyReview",
)
async def update_my_review(
    review_id: str,
    body: UpdateMyReviewRequest,
    customer_user: CustomerUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> UpdateMyReviewResponse:
    use_case = UpdateMyReviewUseCase(db_session=db_session, review_repo=review_repo)
    result = await use_case.execute(
        UpdateMyReviewCommand(
            user_id=customer_user.id,
            review_id=review_id,
            rating=body.rating,
            comment=body.comment,
            fields_to_update=frozenset(body.model_fields_set),
        )
    )
    return UpdateMyReviewResponse(
        id=result.id,
        book_id=result.book_id,
        user_id=result.user_id,
        order_item_id=result.order_item_id,
        rating=result.rating,
        comment=result.comment,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.delete(
    "/me/reviews/{review_id}",
    status_code=204,
    response_model=None,
    operation_id="softDeleteMyReview",
)
async def soft_delete_my_review(
    review_id: str,
    customer_user: CustomerUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> None:
    use_case = SoftDeleteMyReviewUseCase(db_session=db_session, review_repo=review_repo)
    await use_case.execute(
        SoftDeleteMyReviewCommand(user_id=customer_user.id, review_id=review_id)
    )


# user management
@router.get(
    "",
    response_model=PaginatedResponse[UserListItemResponse],
    operation_id="findUsers",
)
async def find_users(
    query_params: Annotated[FindUsersQueryRequest, Depends(FindUsersQueryRequest)],
    _admin_user: AdminUser,
    user_repo: UserRepo,
    db_session: DbSession,
) -> PaginatedResponse[UserListItemResponse]:
    use_case = FindUsersUseCase(db_session=db_session, user_repo=user_repo)
    result = await use_case.execute(query_params.to_command())
    return PaginatedResponse(
        items=[
            UserListItemResponse(
                id=u.id,
                email=u.email,
                full_name=u.full_name,
                date_of_birth=u.date_of_birth,
                role=u.role,
                status=u.status,
                avatar_url=build_public_url(u.avatar_url),
                have_password=u.have_password,
                last_login_at=u.last_login_at,
                created_at=u.created_at,
                updated_at=u.updated_at,
            )
            for u in result.items
        ],
        pagination=PaginationMeta.from_result(result),
    )


@router.get(
    "/{user_id}", response_model=UserProfileResponse, operation_id="viewUserProfile"
)
async def view_user_profile(
    user_id: str,
    _admin_user: AdminUser,
    user_repo: UserRepo,
    db_session: DbSession,
) -> UserProfileResponse:
    use_case = ViewUserProfileUseCase(db_session=db_session, user_repo=user_repo)
    result = await use_case.execute(ViewUserProfileCommand(user_id=user_id))
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


@router.post(
    "/admin",
    response_model=UserProfileResponse,
    status_code=201,
    operation_id="registerAdmin",
)
async def register_admin(
    body: RegisterAdminRequest,
    _admin_user: AdminUser,
    user_repo: UserRepo,
    account_repo: AccountRepo,
    hasher: PasswordHasher,
    db_session: DbSession,
) -> UserProfileResponse:
    use_case = RegisterAdminUseCase(
        db_session=db_session,
        user_repo=user_repo,
        account_repo=account_repo,
        hasher=hasher,
    )
    result = await use_case.execute(
        RegisterAdminCommand(
            email=str(body.email),
            password=body.password,
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


@router.patch(
    "/{user_id}/suspend",
    response_model=UserProfileResponse,
    operation_id="suspendUser",
)
async def suspend_user(
    user_id: str,
    _admin_user: AdminUser,
    user_repo: UserRepo,
    db_session: DbSession,
) -> UserProfileResponse:
    use_case = SuspendUserUseCase(db_session=db_session, user_repo=user_repo)
    result = await use_case.execute(SuspendUserCommand(user_id=user_id))
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
