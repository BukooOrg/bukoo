from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.order_dto import (
    CancelOrderCommand,
    PlaceOrderCommand,
    UpdateOrderStatusCommand,
    ViewOrderDetailCommand,
)
from app.application.dtos.payment_dto import (
    CardDetails,
    OnlineBankingDetails,
    PayOrderCommand,
)
from app.application.use_cases.order import (
    CancelOrderUseCase,
    PayOrderUseCase,
    PlaceOrderUseCase,
    UpdateOrderStatusUseCase,
    ViewOrderDetailUseCase,
)
from app.presentation.dependencies.deps import (
    AddressRepo,
    AdminUser,
    BookRepo,
    CartRepo,
    CurrentUser,
    CustomerUser,
    DbSession,
    EmailNotificationService,
    NotificationRepo,
    OrderRepo,
    PaymentRepo,
    PaymentSvc,
    UserRepo,
)
from app.presentation.schemas.order_schema import (
    BaseOrderItemResponse,
    CancelOrderResponse,
    CardPaymentRequest,
    OnlineBankingPaymentRequest,
    PaymentSummaryResponse,
    PayOrderRequest,
    PayOrderResponse,
    PlaceOrderRequest,
    PlaceOrderResponse,
    UpdateOrderStatusRequest,
    UpdateOrderStatusResponse,
    ViewOrderDetailResponse,
)

router = APIRouter(prefix="/orders", tags=["order"])


@router.post(
    "", status_code=201, response_model=PlaceOrderResponse, operation_id="placeOrder"
)
async def place_order(
    body: PlaceOrderRequest,
    customer_user: CustomerUser,
    book_repo: BookRepo,
    cart_repo: CartRepo,
    address_repo: AddressRepo,
    order_repo: OrderRepo,
    db_session: DbSession,
) -> PlaceOrderResponse:
    use_case = PlaceOrderUseCase(
        db_session=db_session,
        cart_repo=cart_repo,
        book_repo=book_repo,
        address_repo=address_repo,
        order_repo=order_repo,
    )
    result = await use_case.execute(
        PlaceOrderCommand(user_id=customer_user.id, cart_item_ids=body.cart_item_ids)
    )
    return PlaceOrderResponse(
        id=result.id,
        status=result.status,
        subtotal=result.subtotal,
        shipping_cost=result.shipping_cost,
        total=result.total,
        address_snapshot=result.address_snapshot,
        items=[
            BaseOrderItemResponse(
                id=item.id,
                book_id=item.book_id,
                book_title=item.book_title,
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in result.items
        ],
        created_at=result.created_at,
    )


@router.post(
    "/{order_id}/payment",
    status_code=200,
    response_model=PayOrderResponse,
    operation_id="payOrder",
)
async def pay_order(
    order_id: str,
    body: PayOrderRequest,
    customer_user: CustomerUser,
    order_repo: OrderRepo,
    payment_repo: PaymentRepo,
    notification_repo: NotificationRepo,
    payment_svc: PaymentSvc,
    book_repo: BookRepo,
    email_notification_svc: EmailNotificationService,
    db_session: DbSession,
) -> PayOrderResponse:
    online_banking_details: OnlineBankingDetails | None = None
    card_details: CardDetails | None = None

    if isinstance(body, OnlineBankingPaymentRequest):
        online_banking_details = OnlineBankingDetails(
            bank_name=body.bank_name,
            account_number=body.account_number,
        )
    elif isinstance(body, CardPaymentRequest):
        card_details = CardDetails(
            card_number=body.card_number,
            expiry_date=body.expiry_date,
            cvv=body.cvv,
        )

    use_case = PayOrderUseCase(
        db_session=db_session,
        order_repo=order_repo,
        payment_repo=payment_repo,
        notification_repo=notification_repo,
        payment_svc=payment_svc,
        book_repo=book_repo,
        email_notification_svc=email_notification_svc,
    )
    result = await use_case.execute(
        PayOrderCommand(
            order_id=order_id,
            user_id=customer_user.id,
            user_email=customer_user.email,
            user_full_name=customer_user.full_name,
            payment_method=body.payment_method,
            outcome=body.outcome,
            online_banking_details=online_banking_details,
            card_details=card_details,
        )
    )
    return PayOrderResponse(
        order_id=result.order_id,
        order_status=result.order_status,
        payment=PaymentSummaryResponse(
            id=result.payment.id,
            method=result.payment.method,
            amount=result.payment.amount,
            status=result.payment.status,
            simulated_ref=result.payment.simulated_ref,
            created_at=result.payment.created_at,
        ),
    )


@router.get(
    "/{order_id}",
    response_model=ViewOrderDetailResponse,
    operation_id="viewOrderDetail",
)
async def view_order_detail(
    order_id: str,
    current_user: CurrentUser,
    order_repo: OrderRepo,
    db_session: DbSession,
) -> ViewOrderDetailResponse:
    use_case = ViewOrderDetailUseCase(db_session=db_session, order_repo=order_repo)
    result = await use_case.execute(
        ViewOrderDetailCommand(
            order_id=order_id, user_id=current_user.id, user_role=current_user.role
        )
    )
    payment: PaymentSummaryResponse | None = None
    if result.payment is not None:
        payment = PaymentSummaryResponse(
            id=result.payment.id,
            method=result.payment.method,
            amount=result.payment.amount,
            status=result.payment.status,
            simulated_ref=result.payment.simulated_ref,
            created_at=result.payment.created_at,
        )
    return ViewOrderDetailResponse(
        id=result.id,
        user_id=result.user_id,
        status=result.status,
        subtotal=result.subtotal,
        shipping_cost=result.shipping_cost,
        total=result.total,
        address_snapshot=result.address_snapshot,
        items=[
            BaseOrderItemResponse(
                id=item.id,
                book_id=item.book_id,
                book_title=item.book_title,
                unit_price=item.unit_price,
                quantity=item.quantity,
                line_total=item.line_total,
            )
            for item in result.items
        ],
        payment=payment,
        created_at=result.created_at,
        updated_at=result.updated_at,
    )


@router.post(
    "/{order_id}/cancel", response_model=CancelOrderResponse, operation_id="cancelOrder"
)
async def cancel_order(
    order_id: str,
    current_user: CurrentUser,
    order_repo: OrderRepo,
    notification_repo: NotificationRepo,
    book_repo: BookRepo,
    user_repo: UserRepo,
    email_notification_svc: EmailNotificationService,
    db_session: DbSession,
) -> CancelOrderResponse:
    use_case = CancelOrderUseCase(
        db_session=db_session,
        order_repo=order_repo,
        notification_repo=notification_repo,
        book_repo=book_repo,
        user_repo=user_repo,
        email_notification_svc=email_notification_svc,
    )
    result = await use_case.execute(
        CancelOrderCommand(
            order_id=order_id, user_id=current_user.id, user_role=current_user.role
        )
    )
    return CancelOrderResponse(
        id=result.id, status=result.status, updated_at=result.updated_at
    )


@router.patch(
    "/{order_id}/status",
    response_model=UpdateOrderStatusResponse,
    operation_id="updateOrderStatus",
)
async def update_order_status(
    order_id: str,
    body: UpdateOrderStatusRequest,
    _admin: AdminUser,
    order_repo: OrderRepo,
    notification_repo: NotificationRepo,
    user_repo: UserRepo,
    email_notification_svc: EmailNotificationService,
    db_session: DbSession,
) -> UpdateOrderStatusResponse:
    use_case = UpdateOrderStatusUseCase(
        db_session=db_session,
        order_repo=order_repo,
        user_repo=user_repo,
        notification_repo=notification_repo,
        email_notification_svc=email_notification_svc,
    )
    result = await use_case.execute(
        UpdateOrderStatusCommand(order_id=order_id, status=body.status)
    )
    return UpdateOrderStatusResponse(
        id=result.id, status=result.status, updated_at=result.updated_at
    )
