from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.dtos.notification_dto import (
    GetUnreadNotificationCountCommand,
    MarkNotificationAsReadCommand,
)
from app.application.use_cases.notification import (
    FindNotificationsUseCase,
    GetUnreadNotificationCountUseCase,
    MarkNotificationAsReadUseCase,
)
from app.core.constants import UserRole
from app.presentation.dependencies.deps import CurrentUser, DbSession, NotificationRepo
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta
from app.presentation.schemas.notification_schema import (
    BaseNotificationItemResponse,
    MarkNotificationAsReadResponse,
    NotificationListQueryRequest,
    UnreadNotificationCountResponse,
)

router = APIRouter(prefix="/notifications", tags=["notification"])


@router.get(
    "",
    response_model=PaginatedResponse[BaseNotificationItemResponse],
    operation_id="findNotifications",
)
async def find_notifications(
    query_params: Annotated[
        NotificationListQueryRequest, Depends(NotificationListQueryRequest)
    ],
    current_user: CurrentUser,
    notification_repo: NotificationRepo,
    db_session: DbSession,
) -> PaginatedResponse[BaseNotificationItemResponse]:
    use_case = FindNotificationsUseCase(
        db_session=db_session, notification_repo=notification_repo
    )
    result = await use_case.execute(query_params.to_command(current_user.id))
    return PaginatedResponse(
        items=[
            BaseNotificationItemResponse(
                id=item.id,
                user_id=item.user_id,
                type=item.type,
                subject=item.subject,
                body=item.body,
                is_read=item.is_read,
                read_at=item.read_at,
                created_at=item.created_at,
            )
            for item in result.items
        ],
        pagination=PaginationMeta.from_result(result),
    )


@router.get(
    "/unread-count",
    response_model=UnreadNotificationCountResponse,
    operation_id="getUnreadNotificationCount",
)
async def get_unread_notification_count(
    current_user: CurrentUser,
    notification_repo: NotificationRepo,
    db_session: DbSession,
) -> UnreadNotificationCountResponse:
    use_case = GetUnreadNotificationCountUseCase(
        db_session=db_session, notification_repo=notification_repo
    )
    result = await use_case.execute(
        GetUnreadNotificationCountCommand(user_id=current_user.id)
    )
    return UnreadNotificationCountResponse(unread_count=result.unread_count)


@router.patch(
    "/{notification_id}/read",
    response_model=MarkNotificationAsReadResponse,
    operation_id="markNotificationAsRead",
)
async def mark_notification_as_read(
    notification_id: str,
    current_user: CurrentUser,
    notification_repo: NotificationRepo,
    db_session: DbSession,
) -> MarkNotificationAsReadResponse:
    use_case = MarkNotificationAsReadUseCase(
        db_session=db_session, notification_repo=notification_repo
    )
    result = await use_case.execute(
        MarkNotificationAsReadCommand(
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
            notification_id=notification_id,
        )
    )
    return MarkNotificationAsReadResponse(
        id=result.id,
        user_id=result.user_id,
        type=result.type,
        subject=result.subject,
        body=result.body,
        is_read=result.is_read,
        read_at=result.read_at,
        created_at=result.created_at,
    )
