from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.report_job_dtos import (
    FindReportJobsCommand,
    ReportJobListItemResult,
)
from app.core.query_params import PaginatedResult
from app.domain.repositories.report_job_repository import (
    IReportJobRepository,
    ReportJobFilter,
)

from ..base import BaseUseCase


class FindReportJobsUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        report_job_repo: IReportJobRepository,
    ) -> None:
        super().__init__(db_session)
        self._report_job_repo = report_job_repo

    @override
    async def execute(
        self, cmd: FindReportJobsCommand
    ) -> PaginatedResult[ReportJobListItemResult]:
        result = await self._report_job_repo.find_all(
            query=cmd.query_params,
            filters=ReportJobFilter(status=cmd.status, report_type=cmd.report_type),
        )
        return PaginatedResult(
            items=[
                ReportJobListItemResult(
                    id=job.id,
                    report_type=job.report_type,
                    date_from=job.date_from,
                    date_to=job.date_to,
                    report_format=job.report_format,
                    limit=job.limit,
                    status=job.status,
                    created_at=job.created_at,
                    completed_at=job.completed_at,
                )
                for job in result.items
            ],
            total_items=result.total_items,
            page=result.page,
            page_size=result.page_size,
        )
