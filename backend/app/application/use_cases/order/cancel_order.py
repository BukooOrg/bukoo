from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.order_dto import CancelOrderCommand, CancelOrderResult
from app.application.dtos.payment_dto import (
    PaymentReceiptItem,
)
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.core.constants import (
    ALLOWED_CANCELLED_STATUS_FOR_ADMIN,
    NotificationStatus,
    NotificationType,
    OrderStatus,
    UserRole,
)
from app.core.util import construct_order_ref
from app.domain.entities import NotificationEntity
from app.domain.exceptions import (
    OrderAccessDeniedError,
    OrderNotCancellableError,
    OrderNotFoundError,
)
from app.domain.repositories import (
    IBookRepository,
    INotificationRepository,
    IOrderRepository,
    IUserRepository,
)

from ..base import BaseUseCase


class CancelOrderUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        order_repo: IOrderRepository,
        notification_repo: INotificationRepository,
        book_repo: IBookRepository,
        user_repo: IUserRepository,
        email_notification_svc: IEmailNotificationService,
    ) -> None:
        super().__init__(db_session=db_session)
        self._order_repo = order_repo
        self._notification_repo = notification_repo
        self._book_repo = book_repo
        self._user_repo = user_repo
        self._email_notification_svc = email_notification_svc

    @override
    async def execute(self, cmd: CancelOrderCommand) -> CancelOrderResult:
        order = await self._order_repo.find_by_id(cmd.order_id)
        if order is None:
            raise OrderNotFoundError(cmd.order_id)

        if cmd.user_role == UserRole.USER:
            if cmd.user_id != order.user_id:
                raise OrderAccessDeniedError()
            if order.status != OrderStatus.PENDING:
                raise OrderNotCancellableError(order.id, order.status)
        elif cmd.user_role == UserRole.ADMIN:
            if order.status not in ALLOWED_CANCELLED_STATUS_FOR_ADMIN:
                raise OrderNotCancellableError(order.id, order.status, True)

        order.cancel()
        for item in order.order_items:
            book = item.book
            if book is not None:
                book.increase_stock(item.quantity)
                await self._book_repo.save(book)
        await self._order_repo.save(order)

        assert order.user_id is not None
        owner = await self._user_repo.find_by_id(order.user_id)
        if owner is not None:
            now = datetime.now(UTC)
            notification = NotificationEntity(
                _id=str(uuid7()),
                _user_id=order.user_id,
                _type=NotificationType.ORDER_CANCELLED,
                _subject="Order Cancelled",
                _body=f"Your order {construct_order_ref(order.id)} has been cancelled. If you did not request this, please contact support.",
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
            self._email_notification_svc.send_order_cancellation(
                to=owner.email,
                full_name=owner.full_name,
                order_id=order.id,
                items=receipt_items,
                total=order.total,
                cancelled_at=order.updated_at,
            )

        return CancelOrderResult(
            id=order.id, status=order.status, updated_at=order.updated_at
        )
