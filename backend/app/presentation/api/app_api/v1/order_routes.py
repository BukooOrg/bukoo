from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.order_dto import PlaceOrderCommand
from app.application.use_cases.order import PlaceOrderUseCase
from app.presentation.dependencies.deps import (
    AddressRepo,
    BookRepo,
    CartRepo,
    CustomerUser,
    DbSession,
    OrderRepo,
)
from app.presentation.schemas.order_schema import (
    BaseOrderItemResponse,
    PlaceOrderRequest,
    PlaceOrderResponse,
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
