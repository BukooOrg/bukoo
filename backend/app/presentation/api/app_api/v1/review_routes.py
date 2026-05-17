from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.dtos.review_dto import (
    HideOrRestoreReviewCommand,
)
from app.application.use_cases.review import (
    FindReviewsByAdminUseCase,
    HideOrRestoreReviewUseCase,
)
from app.core.util import build_public_url
from app.presentation.dependencies.deps import AdminUser, DbSession, ReviewRepo
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta
from app.presentation.schemas.review_schema import (
    AdminReviewItemResponse,
    AdminReviewListQueryRequest,
    BaseReviewBookItem,
    HideOrRestoreReviewRequest,
    HideOrRestoreReviewResponse,
)

router = APIRouter(prefix="/reviews", tags=["review"])


@router.get(
    "",
    response_model=PaginatedResponse[AdminReviewItemResponse],
    operation_id="findReviewsByAdmin",
)
async def find_reviews_by_admin(
    query_params: Annotated[
        AdminReviewListQueryRequest, Depends(AdminReviewListQueryRequest)
    ],
    _admin_user: AdminUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> PaginatedResponse[AdminReviewItemResponse]:
    use_case = FindReviewsByAdminUseCase(db_session=db_session, review_repo=review_repo)
    result = await use_case.execute(query_params.to_command())
    return PaginatedResponse(
        items=[
            AdminReviewItemResponse(
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
    "/{review_id}/visibility",
    response_model=HideOrRestoreReviewResponse,
    operation_id="hideOrRestoreReview",
)
async def hide_or_restore_review(
    review_id: str,
    body: HideOrRestoreReviewRequest,
    _admin_user: AdminUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> HideOrRestoreReviewResponse:
    use_case = HideOrRestoreReviewUseCase(
        db_session=db_session, review_repo=review_repo
    )
    result = await use_case.execute(
        HideOrRestoreReviewCommand(review_id=review_id, is_hidden=body.is_hidden)
    )
    return HideOrRestoreReviewResponse(
        id=result.id,
        book_id=result.book_id,
        user_id=result.user_id,
        order_item_id=result.order_item_id,
        rating=result.rating,
        comment=result.comment,
        is_hidden=result.is_hidden,
        hidden_at=result.hidden_at,
        created_at=result.created_at,
        updated_at=result.updated_at,
        book=BaseReviewBookItem(
            id=result.book.id,
            title=result.book.title,
            cover_url=build_public_url(result.book.cover_url),
        ),
    )
