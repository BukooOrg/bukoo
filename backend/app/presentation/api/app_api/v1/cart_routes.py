from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.cart_dtos import AddCartItemCommand
from app.application.use_cases.cart import AddCartItemUseCase
from app.core.util import build_public_url
from app.presentation.dependencies.deps import (
    BookRepo,
    CartRepo,
    CurrentUser,
    DbSession,
)
from app.presentation.schemas.cart_schema import (
    AddCartItemRequest,
    AddCartItemResponse,
    CartItemBookResponse,
)

router = APIRouter(prefix="/cart", tags=["cart"])


@router.post("/items", status_code=201, response_model=AddCartItemResponse)
async def add_cart_item(
    body: AddCartItemRequest,
    current_user: CurrentUser,
    db_session: DbSession,
    book_repo: BookRepo,
    cart_repo: CartRepo,
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
            user_id=current_user.id,
        )
    )
    return AddCartItemResponse(
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
