from __future__ import annotations

from fastapi import APIRouter, Response

from app.application.dtos.cart_dtos import (
    AddCartItemCommand,
    ClearAllCartItemsCommand,
    GetMyCartCommand,
    RemoveCartItemCommand,
    UpdateCartItemQuantityCommand,
)
from app.application.use_cases.cart import (
    AddCartItemUseCase,
    ClearAllCartItemsUseCase,
    GetMyCartUseCase,
    RemoveCartItemUseCase,
    UpdateCartItemQuantityUseCase,
)
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
    ClearAllCartItemsResponse,
    GetMyCartResponse,
    UpdateCartItemQuantityRequest,
    UpdateCartItemQuantityResponse,
    build_base_cart_item_response,
)

router = APIRouter(prefix="/cart", tags=["cart"])


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


@router.delete(
    "/items/{item_id}",
    status_code=204,
    response_model=None,
    operation_id="removeCartItem",
)
async def remove_cart_item(
    item_id: str,
    customer_user: CustomerUser,
    cart_repo: CartRepo,
    db_session: DbSession,
) -> Response:
    use_case = RemoveCartItemUseCase(db_session=db_session, cart_repo=cart_repo)
    await use_case.execute(
        RemoveCartItemCommand(item_id=item_id, user_id=customer_user.id)
    )
    return Response(status_code=204)


@router.delete(
    "",
    response_model=ClearAllCartItemsResponse,
    operation_id="clearAllCartItems",
)
async def clear_all_cart_items(
    customer_user: CustomerUser,
    cart_repo: CartRepo,
    db_session: DbSession,
) -> ClearAllCartItemsResponse:
    use_case = ClearAllCartItemsUseCase(db_session=db_session, cart_repo=cart_repo)
    result = await use_case.execute(ClearAllCartItemsCommand(user_id=customer_user.id))
    return ClearAllCartItemsResponse(id=result.id, items=result.items)
