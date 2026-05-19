from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.order_dto import (
    UpdateOrderStatusCommand,
    UpdateOrderStatusResult,
)
from app.application.dtos.payment_dto import PaymentReceiptItem
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.core.constants import (
    ALLOWED_UPDATE_STATUS_FOR_ADMIN,
    ORDER_STATUS_TRANSITION_MAP,
    NotificationStatus,
    NotificationType,
    OrderStatus,
)
from app.core.util import construct_order_ref
from app.domain.entities import NotificationEntity
from app.domain.exceptions import (
    OrderNotFoundError,
    OrderStatusTransitionInvalidError,
)
from app.domain.repositories import (
    INotificationRepository,
    IOrderRepository,
    IUserRepository,
)

from ..base import BaseUseCase


class UpdateOrderStatusUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        order_repo: IOrderRepository,
        user_repo: IUserRepository,
        notification_repo: INotificationRepository,
        email_notification_svc: IEmailNotificationService,
    ) -> None:
        super().__init__(db_session=db_session)
        self._order_repo = order_repo
        self._user_repo = user_repo
        self._notification_repo = notification_repo
        self._email_notification_svc = email_notification_svc

    @override
    async def execute(self, cmd: UpdateOrderStatusCommand) -> UpdateOrderStatusResult:
        order = await self._order_repo.find_by_id(cmd.order_id)
        if order is None:
            raise OrderNotFoundError(cmd.order_id)

        if cmd.status not in ALLOWED_UPDATE_STATUS_FOR_ADMIN:
            raise OrderStatusTransitionInvalidError()

        next_status = ORDER_STATUS_TRANSITION_MAP.get(order.status, None)
        if next_status is None:
            raise OrderStatusTransitionInvalidError()
        if cmd.status != next_status:
            raise OrderStatusTransitionInvalidError()

        order.update_status(cmd.status)
        await self._order_repo.save(order)

        assert order.user_id is not None
        owner = await self._user_repo.find_by_id(order.user_id)
        if owner is not None:
            now = datetime.now(UTC)
            if order.status == OrderStatus.SHIPPED:
                notification = NotificationEntity(
                    _id=str(uuid7()),
                    _user_id=order.user_id,
                    _type=NotificationType.ORDER_SHIPPED,
                    _subject="Order Shipped Out",
                    _body=f"Your order {construct_order_ref(order.id)} has been shipped out.",
                    _status=NotificationStatus.PENDING,
                    _created_at=now,
                    _sent_at=None,
                )
            elif order.status == OrderStatus.DELIVERED:
                notification = NotificationEntity(
                    _id=str(uuid7()),
                    _user_id=order.user_id,
                    _type=NotificationType.ORDER_DELIVERED,
                    _subject="Order Delivered",
                    _body=f"Your order {construct_order_ref(order.id)} has been delivered.",
                    _status=NotificationStatus.PENDING,
                    _created_at=now,
                    _sent_at=None,
                )

            await self._notification_repo.save(notification)

        await self._db_session.commit()

        if owner is not None:
            receipt_items = [
                PaymentReceiptItem(
                    book_title=item.book_title,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in order.order_items
            ]
            if order.status == OrderStatus.SHIPPED:
                self._email_notification_svc.send_order_shipped(
                    to=owner.email,
                    full_name=owner.full_name,
                    order_id=order.id,
                    notification_id=notification.id,
                    items=receipt_items,
                    total=order.total,
                    shipped_at=order.updated_at,
                )
            elif order.status == OrderStatus.DELIVERED:
                self._email_notification_svc.send_order_delivered(
                    to=owner.email,
                    full_name=owner.full_name,
                    order_id=order.id,
                    notification_id=notification.id,
                    items=receipt_items,
                    total=order.total,
                    delivered_at=order.updated_at,
                )

        return UpdateOrderStatusResult(
            id=order.id, status=order.status, updated_at=order.updated_at
        )
