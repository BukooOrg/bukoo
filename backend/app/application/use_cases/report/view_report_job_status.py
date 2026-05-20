from __future__ import annotations

from typing import override

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.report_job_dtos import (
    ViewReportJobStatusCommand,
    ViewReportJobStatusResult,
)
from app.application.interfaces.storage_service import IStorageService
from app.core.constants import ReportJobStatus
from app.domain.exceptions.report import ReportJobNotFoundError
from app.domain.repositories.report_job_repository import IReportJobRepository

from ..base import BaseUseCase


class ViewReportJobStatusUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        report_job_repo: IReportJobRepository,
        storage_svc: IStorageService,
    ) -> None:
        super().__init__(db_session)
        self._report_job_repo = report_job_repo
        self._storage_svc = storage_svc

    @override
    async def execute(
        self, command: ViewReportJobStatusCommand
    ) -> ViewReportJobStatusResult:
        job = await self._report_job_repo.find_by_id(command.job_id)
        if job is None:
            raise ReportJobNotFoundError(command.job_id)

        download_url: str | None = None
        if job.status == ReportJobStatus.COMPLETED and job.file_key is not None:
            download_url = await self._storage_svc.get_presigned_url(job.file_key)

        return ViewReportJobStatusResult(
            job_id=job.id,
            status=job.status,
            created_at=job.created_at,
            completed_at=job.completed_at,
            download_url=download_url,
        )
