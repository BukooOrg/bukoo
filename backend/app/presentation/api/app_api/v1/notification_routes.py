from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response

from app.application.dtos.notification_dto import (
    DeleteNotificationCommand,
    GetUnreadNotificationCountCommand,
    MarkAllNotificationsAsReadCommand,
    MarkNotificationAsReadCommand,
)
from app.application.use_cases.notification import (
    DeleteNotificationUseCase,
    FindNotificationsUseCase,
    GetUnreadNotificationCountUseCase,
    MarkAllNotificationsAsReadUseCase,
    MarkNotificationAsReadUseCase,
)
from app.core.constants import UserRole
from app.presentation.dependencies.deps import (
    CurrentUser,
    DbSession,
    NotificationRepo,
    UserRepo,
)
from app.presentation.schemas.list_schema import PaginatedResponse, PaginationMeta
from app.presentation.schemas.notification_schema import (
    BaseNotificationItemResponse,
    MarkAllNotificationsAsReadResponse,
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
    target_user_id = None if current_user.role == UserRole.ADMIN else current_user.id
    result = await use_case.execute(query_params.to_command(target_user_id))
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
    # Admins don't receive personal notifications
    if current_user.role == UserRole.ADMIN:
        return UnreadNotificationCountResponse(unread_count=0)
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


@router.patch(
    "/read-all",
    response_model=MarkAllNotificationsAsReadResponse,
    operation_id="markAllNotificationsAsRead",
)
async def mark_all_notifications_as_read(
    current_user: CurrentUser,
    notification_repo: NotificationRepo,
    user_repo: UserRepo,
    db_session: DbSession,
    user_id: str | None = Query(None),
) -> MarkAllNotificationsAsReadResponse:
    use_case = MarkAllNotificationsAsReadUseCase(
        db_session=db_session,
        notification_repo=notification_repo,
        user_repo=user_repo,
    )
    result = await use_case.execute(
        MarkAllNotificationsAsReadCommand(
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
            target_user_id=user_id,
        )
    )
    return MarkAllNotificationsAsReadResponse(marked_count=result.marked_count)


@router.delete(
    "/{notification_id}",
    status_code=204,
    response_model=None,
    operation_id="deleteNotification",
)
async def delete_notification(
    notification_id: str,
    current_user: CurrentUser,
    notification_repo: NotificationRepo,
    db_session: DbSession,
) -> Response:
    use_case = DeleteNotificationUseCase(
        db_session=db_session, notification_repo=notification_repo
    )
    await use_case.execute(
        DeleteNotificationCommand(
            user_id=current_user.id,
            is_admin=current_user.role == UserRole.ADMIN,
            notification_id=notification_id,
        )
    )
    return Response(status_code=204)
