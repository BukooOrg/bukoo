from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.payment_dto import (
    PaymentProcessResult,
    PaymentReceiptItem,
    PaymentSummaryResult,
    PayOrderCommand,
    PayOrderResult,
    ProcessPaymentCommand,
)
from app.application.interfaces.email_notification_service import (
    IEmailNotificationService,
)
from app.application.interfaces.payment_service import IPaymentService
from app.application.interfaces.payment_strategy import IPaymentStrategy
from app.core.constants import (
    NotificationStatus,
    NotificationType,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.core.util import construct_order_ref
from app.domain.entities import NotificationEntity, PaymentEntity
from app.domain.exceptions import OrderNotFoundError, OrderNotPayableError
from app.domain.repositories import (
    IBookRepository,
    INotificationRepository,
    IOrderRepository,
    IPaymentRepository,
)
from app.domain.repositories.book_repository import BookStatusFilter
from app.infrastructure.payment.strategies import (
    CardPaymentStrategy,
    OnlineBankingPaymentStrategy,
)

from ..base import BaseUseCase


class PayOrderUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        order_repo: IOrderRepository,
        payment_repo: IPaymentRepository,
        notification_repo: INotificationRepository,
        payment_svc: IPaymentService,
        book_repo: IBookRepository,
        email_notification_svc: IEmailNotificationService,
    ) -> None:
        super().__init__(db_session=db_session)
        self._order_repo = order_repo
        self._payment_repo = payment_repo
        self._notification_repo = notification_repo
        self._payment_svc = payment_svc
        self._book_repo = book_repo
        self._email_notification_svc = email_notification_svc

    async def _process_payment(
        self, cmd: ProcessPaymentCommand
    ) -> PaymentProcessResult:
        strategy: IPaymentStrategy
        if cmd.payment_method == PaymentMethod.ONLINE_BANKING:
            assert cmd.online_banking_details is not None
            strategy = OnlineBankingPaymentStrategy(
                bank_name=cmd.online_banking_details.bank_name,
                account_number=cmd.online_banking_details.account_number,
            )
        else:
            assert cmd.card_details is not None
            strategy = CardPaymentStrategy(
                card_number=cmd.card_details.card_number,
                expiry_date=cmd.card_details.expiry_date,
                cvv=cmd.card_details.cvv,
            )

        self._payment_svc.set_strategy(strategy)
        return await self._payment_svc.execute_payment(cmd)

    @override
    async def execute(self, cmd: PayOrderCommand) -> PayOrderResult:
        order = await self._order_repo.find_by_id(cmd.order_id)
        if order is None:
            raise OrderNotFoundError(cmd.order_id)

        if order.user_id != cmd.user_id:
            raise OrderNotFoundError(cmd.order_id)

        if order.status != OrderStatus.PENDING:
            raise OrderNotPayableError(cmd.order_id, order.status)

        result = await self._process_payment(
            ProcessPaymentCommand(
                order_id=order.id,
                amount=order.total,
                payment_method=cmd.payment_method,
                outcome=cmd.outcome,
                online_banking_details=cmd.online_banking_details,
                card_details=cmd.card_details,
            )
        )

        now = datetime.now(UTC)
        payment = PaymentEntity(
            _id=str(uuid7()),
            _order_id=order.id,
            _method=result.method,
            _amount=order.total,
            _status=PaymentStatus.PENDING,
            _simulated_ref=None,
            _created_at=now,
            _updated_at=now,
        )

        if result.success:
            assert result.simulated_ref is not None
            payment.mark_success(result.simulated_ref)
            order.mark_paid()

            # todo: decide when to update sent_at
            notification = NotificationEntity(
                _id=str(uuid7()),
                _user_id=cmd.user_id,
                _type=NotificationType.PAYMENT_SUCCESS,
                _subject="Payment Confirmed",
                _body=(
                    f"Your payment for order {construct_order_ref(order.id)} "
                    f"has been confirmed. Total paid: RM {order.total:.2f}."
                ),
                _status=NotificationStatus.PENDING,
                _created_at=now,
                _sent_at=None,
            )
            await self._notification_repo.save(notification)
        else:
            payment.mark_failed()
            order.cancel()

            for item in order.order_items:
                if item.book_id is not None:
                    book = await self._book_repo.find_by_id(
                        item.book_id, BookStatusFilter()
                    )
                    if book is not None:
                        book.increase_stock(item.quantity)
                        await self._book_repo.save(book)

        await self._payment_repo.save(payment)
        await self._order_repo.save(order)
        await self._db_session.commit()

        if result.success:
            receipt_items = [
                PaymentReceiptItem(
                    book_title=item.book_title,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in order.order_items
            ]
            method_display = (
                "Online Banking"
                if result.method == PaymentMethod.ONLINE_BANKING
                else "Card"
            )
            self._email_notification_svc.send_payment_receipt(
                to=cmd.user_email,
                full_name=cmd.user_full_name,
                order_id=order.id,
                payment_ref=result.simulated_ref or "",
                payment_method_display=method_display,
                items=receipt_items,
                subtotal=order.subtotal,
                shipping_cost=order.shipping_cost,
                total=order.total,
                address_snapshot=order.address_snapshot,
                paid_at=now,
            )

        return PayOrderResult(
            order_id=order.id,
            order_status=order.status,
            payment=PaymentSummaryResult(
                id=payment.id,
                method=payment.method,
                amount=payment.amount,
                status=payment.status,
                simulated_ref=payment.simulated_ref,
                created_at=payment.created_at,
            ),
        )
