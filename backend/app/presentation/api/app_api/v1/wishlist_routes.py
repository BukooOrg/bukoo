from __future__ import annotations

from typing import TypeVar

from fastapi import APIRouter

from app.application.dtos.wishlist_dto import (
    AddWishlistItemCommand,
    BaseWishlistItemResult,
    GetMyWishlistCommand,
)
from app.application.use_cases.wishlist import (
    AddWishlistItemUseCase,
    GetMyWishlistUseCase,
)
from app.core.util import build_public_url
from app.presentation.dependencies.deps import (
    BookRepo,
    CustomerUser,
    DbSession,
    WishlistRepo,
)
from app.presentation.schemas.wishlist_schema import (
    AddWishlistItemRequest,
    AddWishlistItemResponse,
    BaseWishlistItemResponse,
    GetMyWishlistResponse,
    WishlistItemBookResponse,
)

router = APIRouter(prefix="/wishlist", tags=["wishlist"])


T = TypeVar("T", bound=BaseWishlistItemResult)
P = TypeVar("P", bound=BaseWishlistItemResponse)


def build_base_cart_item_response(result: T, response_cls: type[P]) -> P:  # noqa: UP047 # type: ignore
    return response_cls(
        id=result.id,
        wishlist_id=result.wishlist_id,
        book_id=result.book_id,
        added_at=result.added_at,
        book=WishlistItemBookResponse(
            id=result.book.id,
            title=result.book.title,
            price=result.book.price,
            cover_url=build_public_url(result.book.cover_url),
        ),
    )


@router.get("", response_model=GetMyWishlistResponse, operation_id="getMyWishlist")
async def get_my_wishlist(
    customer_user: CustomerUser, wishlist_repo: WishlistRepo, db_session: DbSession
) -> GetMyWishlistResponse:
    use_case = GetMyWishlistUseCase(db_session=db_session, wishlist_repo=wishlist_repo)
    result = await use_case.execute(GetMyWishlistCommand(user_id=customer_user.id))
    return GetMyWishlistResponse(
        id=result.id,
        items=[
            build_base_cart_item_response(item, BaseWishlistItemResponse)
            for item in result.items
        ],
    )


@router.post(
    "/items",
    status_code=201,
    response_model=AddWishlistItemResponse,
    operation_id="addWishlistItem",
)
async def add_wishlist_item(
    body: AddWishlistItemRequest,
    customer_user: CustomerUser,
    book_repo: BookRepo,
    wishlist_repo: WishlistRepo,
    db_session: DbSession,
) -> AddWishlistItemResponse:
    use_case = AddWishlistItemUseCase(
        db_session=db_session,
        book_repo=book_repo,
        wishlist_repo=wishlist_repo,
    )
    result = await use_case.execute(
        AddWishlistItemCommand(
            book_id=body.book_id,
            user_id=customer_user.id,
        )
    )
    return build_base_cart_item_response(result, AddWishlistItemResponse)
