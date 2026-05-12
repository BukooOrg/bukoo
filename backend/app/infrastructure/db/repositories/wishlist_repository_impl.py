from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities import WishlistEntity
from app.domain.repositories import IWishlistRepository
from app.infrastructure.db.mappers.wishlist_item_mapper import WishlistItemMapper
from app.infrastructure.db.mappers.wishlist_mapper import WishlistMapper
from app.infrastructure.db.models import WishlistModel


class WishlistRepositoryImpl(IWishlistRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def find_by_user_id(self, user_id: str) -> WishlistEntity | None:
        stmt = select(WishlistModel).where(WishlistModel.user_id == user_id)
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return WishlistMapper.to_entity(model) if model else None

    @override
    async def save(self, wishlist: WishlistEntity) -> None:
        existing = await self._session.get(WishlistModel, wishlist.id)

        if existing is None:
            wishlist_model = WishlistMapper.to_model(wishlist)
            self._session.add(wishlist_model)
        else:
            existing.updated_at = wishlist.updated_at

        for item in wishlist.wishlist_items:
            item_model = WishlistItemMapper.to_model(item)
            await self._session.merge(item_model)
