from __future__ import annotations

from typing import override

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.repositories.report_job_repository import IReportJobRepository
from app.infrastructure.db.mappers.report_job_mapper import ReportJobMapper
from app.infrastructure.db.models.report_job_model import ReportJobModel


class ReportJobRepositoryImpl(IReportJobRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @override
    async def save(self, job: ReportJobEntity) -> None:
        model = ReportJobMapper.to_model(job)
        await self._session.merge(model)

    @override
    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        stmt = (
            select(ReportJobModel)
            .where(ReportJobModel.id == job_id)
            .where(ReportJobModel.deleted_at.is_(None))
        )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return ReportJobMapper.to_entity(model) if model else None
