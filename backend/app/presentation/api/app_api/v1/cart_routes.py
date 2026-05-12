from __future__ import annotations

from typing import TypeVar

from fastapi import APIRouter

from app.application.dtos.cart_dtos import (
    AddCartItemCommand,
    BaseCartItemResult,
    GetMyCartCommand,
    UpdateCartItemQuantityCommand,
)
from app.application.use_cases.cart import (
    AddCartItemUseCase,
    GetMyCartUseCase,
    UpdateCartItemQuantityUseCase,
)
from app.core.util import build_public_url
from app.presentation.dependencies.deps import (
    BookRepo,
    CartRepo,
    CustomerUser,
    DbSession,
)
from app.presentation.schemas.cart_schema import (
    AddCartItemRequest,
    AddCartItemResponse,
    BaseCartItemResponse,
    CartItemBookResponse,
    GetMyCartResponse,
    UpdateCartItemQuantityRequest,
    UpdateCartItemQuantityResponse,
)

router = APIRouter(prefix="/cart", tags=["cart"])

T = TypeVar("T", bound=BaseCartItemResult)
P = TypeVar("P", bound=BaseCartItemResponse)


def build_base_cart_item_response(result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=result.id,
        cart_id=result.cart_id,
        book_id=result.book_id,
        quantity=result.quantity,
        book=CartItemBookResponse(
            id=result.book.id,
            title=result.book.title,
            price=result.book.price,
            cover_url=build_public_url(result.book.cover_url),
        ),
    )


@router.get("", response_model=GetMyCartResponse, operation_id="getMyCart")
async def get_my_cart(
    customer_user: CustomerUser, cart_repo: CartRepo, db_session: DbSession
) -> GetMyCartResponse:
    use_case = GetMyCartUseCase(db_session=db_session, cart_repo=cart_repo)
    result = await use_case.execute(GetMyCartCommand(user_id=customer_user.id))
    return GetMyCartResponse(
        id=result.id,
        items=[
            build_base_cart_item_response(item, BaseCartItemResponse)
            for item in result.items
        ],
    )


@router.post(
    "/items",
    status_code=201,
    response_model=AddCartItemResponse,
    operation_id="addCartItem",
)
async def add_cart_item(
    body: AddCartItemRequest,
    customer_user: CustomerUser,
    book_repo: BookRepo,
    cart_repo: CartRepo,
    db_session: DbSession,
) -> AddCartItemResponse:
    use_case = AddCartItemUseCase(
        db_session=db_session,
        book_repo=book_repo,
        cart_repo=cart_repo,
    )
    result = await use_case.execute(
        AddCartItemCommand(
            book_id=body.book_id,
            quantity=body.quantity,
            user_id=customer_user.id,
        )
    )
    return build_base_cart_item_response(result, AddCartItemResponse)


@router.patch(
    "/items/{item_id}",
    response_model=UpdateCartItemQuantityResponse,
    operation_id="updateCartItemQuantity",
)
async def update_cart_item_quantity(
    item_id: str,
    body: UpdateCartItemQuantityRequest,
    customer_user: CustomerUser,
    cart_repo: CartRepo,
    db_session: DbSession,
) -> UpdateCartItemQuantityResponse:
    use_case = UpdateCartItemQuantityUseCase(db_session=db_session, cart_repo=cart_repo)
    result = await use_case.execute(
        UpdateCartItemQuantityCommand(
            item_id=item_id, user_id=customer_user.id, quantity=body.quantity
        )
    )
    return build_base_cart_item_response(result, UpdateCartItemQuantityResponse)
