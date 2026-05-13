from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.wishlist_dto import (
    BaseWishlistItemResult,
    GetMyWishlistCommand,
    GetMyWishlistResult,
    WishlistItemBookResult,
)
from app.domain.exceptions import WishlistNotFoundError
from app.domain.repositories import IWishlistRepository

from ..base import BaseUseCase


class GetMyWishlistUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        wishlist_repo: IWishlistRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._wishlist_repo = wishlist_repo

    @override
    async def execute(self, cmd: GetMyWishlistCommand) -> GetMyWishlistResult:
        wishlist = await self._wishlist_repo.find_by_user_id(cmd.user_id)
        if wishlist is None:
            raise WishlistNotFoundError(cmd.user_id)

        items: list[BaseWishlistItemResult] = []
        for item in wishlist.wishlist_items:
            book = item.book
            assert book is not None
            items.append(
                BaseWishlistItemResult(
                    id=item.id,
                    wishlist_id=item.wishlist_id,
                    book_id=item.book_id,
                    added_at=item.added_at,
                    book=WishlistItemBookResult(
                        id=book.id,
                        title=book.title,
                        price=book.price,
                        cover_url=book.cover_url,
                    ),
                )
            )
        return GetMyWishlistResult(id=wishlist.id, items=items)
