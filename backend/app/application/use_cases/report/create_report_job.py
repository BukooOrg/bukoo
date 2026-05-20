from __future__ import annotations

from datetime import UTC, datetime
from typing import override

from sqlalchemy.ext.asyncio import AsyncSession
from uuid_extension import uuid7

from app.application.dtos.report_job_dtos import (
    CreateReportJobCommand,
    CreateReportJobResult,
)
from app.application.interfaces.report_job_service import IReportJobService
from app.core.constants import ReportJobStatus
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.exceptions.report import InvalidReportDateRangeError
from app.domain.repositories.report_job_repository import IReportJobRepository

from ..base import BaseUseCase


class CreateReportJobUseCase(BaseUseCase):
    def __init__(
        self,
        db_session: AsyncSession,
        report_job_repo: IReportJobRepository,
        report_job_svc: IReportJobService,
    ) -> None:
        super().__init__(db_session)
        self._report_job_repo = report_job_repo
        self._report_job_svc = report_job_svc

    @override
    async def execute(self, cmd: CreateReportJobCommand) -> CreateReportJobResult:
        if cmd.date_from >= cmd.date_to:
            raise InvalidReportDateRangeError

        now = datetime.now(UTC)
        job = ReportJobEntity(
            _id=str(uuid7()),
            _admin_id=cmd.admin_id,
            _report_type=cmd.report_type,
            _date_from=cmd.date_from,
            _date_to=cmd.date_to,
            _report_format=cmd.report_format,
            _status=ReportJobStatus.PENDING,
            _limit=cmd.limit,
            _created_at=now,
            _updated_at=now,
        )

        await self._report_job_repo.save(job)
        await self._db_session.commit()

        self._report_job_svc.dispatch_report_job(job.id)

        return CreateReportJobResult(job_id=job.id, status=job.status)
