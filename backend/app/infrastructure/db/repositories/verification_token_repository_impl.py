from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import VerificationTokenType
from app.domain.entities.verification_token_entity import VerificationTokenEntity
from app.domain.repositories.verification_token_repository import (
    IVerificationTokenRepository,
)
from app.infrastructure.db.mappers.verification_token_mapper import (
    VerificationTokenMapper,
)
from app.infrastructure.db.models.verification_token_model import VerificationTokenModel


class VerificationTokenRepositoryImpl(IVerificationTokenRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, token: VerificationTokenEntity) -> None:
        model = VerificationTokenMapper.to_model(token)
        await self._session.merge(model)

    @override
    async def find_active_by_user_and_type(
        self,
        user_id: str,
        token_type: VerificationTokenType,
    ) -> VerificationTokenEntity | None:
        now = datetime.now(UTC)
        stmt = (
            select(VerificationTokenModel)
            .where(VerificationTokenModel.user_id == user_id)
            .where(VerificationTokenModel.type == token_type)
            .where(VerificationTokenModel.used_at.is_(None))
            .where(VerificationTokenModel.expires_at > now)
            .order_by(VerificationTokenModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return VerificationTokenMapper.to_entity(model) if model else None
