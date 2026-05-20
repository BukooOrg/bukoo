from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.report_job_dtos import (
    ViewReportJobStatusCommand,
    ViewReportJobStatusResult,
)
from app.application.use_cases.report.view_report_job_status import (
    ViewReportJobStatusUseCase,
)
from app.core.constants import ReportFormat, ReportJobStatus, ReportType
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.exceptions.report import ReportJobNotFoundError
from app.domain.repositories.report_job_repository import IReportJobRepository


class FakeReportJobRepository(IReportJobRepository):
    def __init__(self) -> None:
        self._store: dict[str, ReportJobEntity] = {}

    async def save(self, job: ReportJobEntity) -> None:
        self._store[job.id] = job

    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        return self._store.get(job_id)


def _make_job(
    status: ReportJobStatus = ReportJobStatus.PENDING,
    file_key: str | None = None,
    completed_at: datetime | None = None,
) -> ReportJobEntity:
    now = datetime.now(UTC)
    return ReportJobEntity(
        _id="job-001",
        _admin_id="admin-001",
        _report_type=ReportType.SALES_SUMMARY,
        _date_from=datetime(2025, 1, 1).date(),
        _date_to=datetime(2025, 12, 31).date(),
        _report_format=ReportFormat.CSV,
        _status=status,
        _created_at=now,
        _updated_at=now,
        _file_key=file_key,
        _completed_at=completed_at,
    )


@pytest.mark.unit
class TestViewReportJobStatusUseCase:
    async def test_returns_pending_result_with_no_download_url(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        storage_svc = AsyncMock()
        job = _make_job(status=ReportJobStatus.PENDING)
        await repo.save(job)

        use_case = ViewReportJobStatusUseCase(
            db_session=db_session,
            report_job_repo=repo,
            storage_svc=storage_svc,
        )
        result = await use_case.execute(ViewReportJobStatusCommand(job_id="job-001"))

        assert isinstance(result, ViewReportJobStatusResult)
        assert result.job_id == "job-001"
        assert result.status == ReportJobStatus.PENDING
        assert result.download_url is None
        assert result.completed_at is None
        storage_svc.get_presigned_url.assert_not_called()

    async def test_returns_completed_result_with_download_url(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        storage_svc = AsyncMock()
        storage_svc.get_presigned_url.return_value = (
            "https://minio.local/report.csv?token=abc"
        )
        completed_at = datetime.now(UTC)
        job = _make_job(
            status=ReportJobStatus.COMPLETED,
            file_key="reports/job-001.csv",
            completed_at=completed_at,
        )
        await repo.save(job)

        use_case = ViewReportJobStatusUseCase(
            db_session=db_session,
            report_job_repo=repo,
            storage_svc=storage_svc,
        )
        result = await use_case.execute(ViewReportJobStatusCommand(job_id="job-001"))

        assert result.status == ReportJobStatus.COMPLETED
        assert result.download_url == "https://minio.local/report.csv?token=abc"
        assert result.completed_at == completed_at
        storage_svc.get_presigned_url.assert_called_once_with("reports/job-001.csv")

    async def test_raises_report_job_not_found_when_missing(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        storage_svc = AsyncMock()

        use_case = ViewReportJobStatusUseCase(
            db_session=db_session,
            report_job_repo=repo,
            storage_svc=storage_svc,
        )
        with pytest.raises(ReportJobNotFoundError):
            await use_case.execute(ViewReportJobStatusCommand(job_id="nonexistent-id"))

    async def test_failed_job_has_no_download_url(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        storage_svc = AsyncMock()
        job = _make_job(status=ReportJobStatus.FAILED)
        await repo.save(job)

        use_case = ViewReportJobStatusUseCase(
            db_session=db_session,
            report_job_repo=repo,
            storage_svc=storage_svc,
        )
        result = await use_case.execute(ViewReportJobStatusCommand(job_id="job-001"))

        assert result.status == ReportJobStatus.FAILED
        assert result.download_url is None
        assert result.completed_at is None
        storage_svc.get_presigned_url.assert_not_called()

    async def test_processing_job_has_no_download_url(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        storage_svc = AsyncMock()
        job = _make_job(status=ReportJobStatus.PROCESSING)
        await repo.save(job)

        use_case = ViewReportJobStatusUseCase(
            db_session=db_session,
            report_job_repo=repo,
            storage_svc=storage_svc,
        )
        result = await use_case.execute(ViewReportJobStatusCommand(job_id="job-001"))

        assert result.status == ReportJobStatus.PROCESSING
        assert result.download_url is None
        storage_svc.get_presigned_url.assert_not_called()
