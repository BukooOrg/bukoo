from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.report_job_dtos import (
    DownloadReportCommand,
    DownloadReportResult,
)
from app.core.constants import ReportJobStatus
from app.domain.exceptions.report import ReportJobNotFoundError, ReportNotReadyError
from app.domain.repositories.report_job_repository import IReportJobRepository

from ..base import BaseUseCase


class DownloadReportUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        report_job_repo: IReportJobRepository,
    ) -> None:
        super().__init__(db_session)
        self._report_job_repo = report_job_repo

    @override
    async def execute(self, cmd: DownloadReportCommand) -> DownloadReportResult:
        job = await self._report_job_repo.find_by_id(cmd.job_id)
        if job is None:
            raise ReportJobNotFoundError(cmd.job_id)

        if job.status != ReportJobStatus.COMPLETED or job.file_key is None:
            raise ReportNotReadyError(cmd.job_id)

        return DownloadReportResult(
            file_key=job.file_key,
            report_format=job.report_format,
            report_type=job.report_type,
            date_from=job.date_from,
            date_to=job.date_to,
        )
