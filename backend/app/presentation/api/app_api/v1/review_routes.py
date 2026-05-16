from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.review_dto import SoftDeleteReviewCommand, UpdateReviewCommand
from app.application.use_cases.review import (
    SoftDeleteReviewUseCase,
    UpdateReviewUseCase,
)
from app.presentation.dependencies.deps import CustomerUser, DbSession, ReviewRepo
from app.presentation.schemas.review_schema import (
    UpdateReviewRequest,
    UpdateReviewResponse,
)

router = APIRouter(prefix="/reviews", tags=["review"])


@router.patch(
    "/{review_id}",
    response_model=UpdateReviewResponse,
    operation_id="updateReview",
)
async def update_review(
    review_id: str,
    body: UpdateReviewRequest,
    customer_user: CustomerUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> UpdateReviewResponse:
    use_case = UpdateReviewUseCase(db_session=db_session, review_repo=review_repo)
    result = await use_case.execute(
        UpdateReviewCommand(
            user_id=customer_user.id,
            review_id=review_id,
            rating=body.rating,
            comment=body.comment,
            fields_to_update=frozenset(body.model_fields_set),
        )
    )
    return UpdateReviewResponse(
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
    "/{review_id}",
    status_code=204,
    response_model=None,
    operation_id="softDeleteReview",
)
async def soft_delete_review(
    review_id: str,
    customer_user: CustomerUser,
    review_repo: ReviewRepo,
    db_session: DbSession,
) -> None:
    use_case = SoftDeleteReviewUseCase(db_session=db_session, review_repo=review_repo)
    await use_case.execute(
        SoftDeleteReviewCommand(user_id=customer_user.id, review_id=review_id)
    )
