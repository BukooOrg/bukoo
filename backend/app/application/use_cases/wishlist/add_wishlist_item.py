from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.wishlist_dto import (
    AddWishlistItemCommand,
    AddWishlistItemResult,
    WishlistItemBookResult,
)
from app.domain.entities import WishlistEntity, WishlistItemEntity
from app.domain.exceptions import BookNotFoundError, WishlistItemAlreadyExistsError
from app.domain.repositories import IBookRepository, IWishlistRepository
from app.domain.repositories.book_repository import BookStatusFilter

from ..base import BaseUseCase


class AddWishlistItemUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        book_repo: IBookRepository,
        wishlist_repo: IWishlistRepository,
    ) -> None:
        super().__init__(db_session=db_session)
        self._book_repo = book_repo
        self._wishlist_repo = wishlist_repo

    @override
    async def execute(self, cmd: AddWishlistItemCommand) -> AddWishlistItemResult:
        book = await self._book_repo.find_by_id(
            cmd.book_id, BookStatusFilter(status="activate")
        )
        if book is None:
            raise BookNotFoundError(cmd.book_id)

        wishlist = await self._wishlist_repo.find_by_user_id(cmd.user_id)
        if wishlist is None:
            now = datetime.now(UTC)
            wishlist = WishlistEntity(
                _id=str(uuid7()), _user_id=cmd.user_id, _created_at=now, _updated_at=now
            )

        existing = wishlist.find_item_by_book_id(cmd.book_id)
        if existing is not None:
            raise WishlistItemAlreadyExistsError(existing.id)

        now = datetime.now(UTC)
        new_item = WishlistItemEntity(
            _id=str(uuid7()),
            _wishlist_id=wishlist.id,
            _book_id=book.id,
            _added_at=now,
            _created_at=now,
            _updated_at=now,
            _book=book,
        )
        wishlist.add_wishlist_item(new_item)

        await self._wishlist_repo.save(wishlist)
        await self._db_session.commit()
        return AddWishlistItemResult(
            id=new_item.id,
            wishlist_id=new_item.wishlist_id,
            book_id=new_item.book_id,
            added_at=new_item.added_at,
            book=WishlistItemBookResult(
                id=book.id, title=book.title, price=book.price, cover_url=book.cover_url
            ),
        )
