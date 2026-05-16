from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.wishlist_dto import RemoveWishlistItemCommand
from app.domain.exceptions import WishlistItemNotFoundError, WishlistNotFoundError
from app.domain.repositories import IWishlistRepository

from ..base import BaseUseCase


class RemoveWishlistItemUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        wishlist_repo: IWishlistRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._wishlist_repo = wishlist_repo

    @override
    async def execute(self, cmd: RemoveWishlistItemCommand) -> None:
        wishlist = await self._wishlist_repo.find_by_user_id(cmd.user_id)
        if wishlist is None:
            raise WishlistNotFoundError(cmd.user_id)

        item = wishlist.find_item_by_item_id(cmd.item_id)
        if item is None:
            raise WishlistItemNotFoundError(cmd.item_id)

        wishlist.remove_wishlist_item(cmd.item_id)
        await self._wishlist_repo.delete_item_by_item_id(cmd.item_id)
        await self._wishlist_repo.save(wishlist)
        await self._db_session.commit()
