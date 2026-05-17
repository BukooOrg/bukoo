from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.review_dto import (
    HideOrRestoreReviewCommand,
)
from app.application.use_cases.review import (
    HideOrRestoreReviewUseCase,
)
from app.presentation.dependencies.deps import AdminUser, DbSession, ReviewRepo
from app.presentation.schemas.review_schema import (
    HideOrRestoreReviewRequest,
    HideOrRestoreReviewResponse,
)

router = APIRouter(prefix="/reviews", tags=["review"])


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
    )
