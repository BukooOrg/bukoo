from __future__ import annotations

from typing import Any, ClassVar, override

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute

from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.repositories.report_job_repository import (
    IReportJobRepository,
    ReportJobFilter,
)
from app.infrastructure.db.mappers.report_job_mapper import ReportJobMapper
from app.infrastructure.db.models.report_job_model import ReportJobModel


class ReportJobRepositoryImpl(IReportJobRepository):
    SORTABLE_FIELDS: ClassVar[dict[str, InstrumentedAttribute[Any]]] = {
        "created_at": ReportJobModel.created_at,
        "completed_at": ReportJobModel.completed_at,
        "status": ReportJobModel.status,
        "report_type": ReportJobModel.report_type,
    }

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

    @override
    async def find_all(
        self, query: QueryParams, filters: ReportJobFilter
    ) -> PaginatedResult[ReportJobEntity]:
        base_stmt = select(ReportJobModel).where(ReportJobModel.deleted_at.is_(None))

        if filters.status is not None:
            base_stmt = base_stmt.where(ReportJobModel.status == filters.status)
        if filters.report_type is not None:
            base_stmt = base_stmt.where(
                ReportJobModel.report_type == filters.report_type
            )

        total_items: int = (
            await self._session.execute(
                select(func.count()).select_from(base_stmt.subquery())
            )
        ).scalar_one()

        order_clauses = [
            self.SORTABLE_FIELDS[s.field].asc()
            if s.direction == "asc"
            else self.SORTABLE_FIELDS[s.field].desc()
            for s in query.sorts
            if s.field in self.SORTABLE_FIELDS
        ]
        if not order_clauses:
            order_clauses = [ReportJobModel.created_at.desc()]

        models = (
            (
                await self._session.execute(
                    base_stmt.order_by(*order_clauses)
                    .offset(query.page.offset)
                    .limit(query.page.limit)
                )
            )
            .scalars()
            .all()
        )

        return PaginatedResult(
            items=[ReportJobMapper.to_entity(m) for m in models],
            total_items=total_items,
            page=query.page.page,
            page_size=query.page.page_size,
        )
