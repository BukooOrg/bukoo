from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.report_job_dtos import (
    DownloadReportCommand,
    DownloadReportResult,
)
from app.application.use_cases.report.download_report import DownloadReportUseCase
from app.core.constants import ReportFormat, ReportJobStatus, ReportType
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.exceptions.report import ReportJobNotFoundError, ReportNotReadyError
from app.domain.repositories.report_job_repository import IReportJobRepository


class FakeReportJobRepository(IReportJobRepository):
    def __init__(self) -> None:
        self._store: dict[str, ReportJobEntity] = {}

    async def save(self, job: ReportJobEntity) -> None:
        self._store[job.id] = job

    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        return self._store.get(job_id)

    async def find_all(self, *args: Any, **kwargs: Any) -> Any:
        pass


def _make_job(
    status: ReportJobStatus = ReportJobStatus.COMPLETED,
    file_key: str | None = "reports/job-001.pdf",
    report_format: ReportFormat = ReportFormat.PDF,
) -> ReportJobEntity:
    now = datetime.now(UTC)
    return ReportJobEntity(
        _id="job-001",
        _admin_id="admin-001",
        _report_type=ReportType.SALES_SUMMARY,
        _date_from=datetime(2025, 1, 1).date(),
        _date_to=datetime(2025, 12, 31).date(),
        _report_format=report_format,
        _status=status,
        _created_at=now,
        _updated_at=now,
        _file_key=file_key,
        _completed_at=now if status == ReportJobStatus.COMPLETED else None,
    )


def _build_use_case(
    repo: FakeReportJobRepository | None = None,
) -> tuple[DownloadReportUseCase, AsyncMock]:
    db_session = AsyncMock()
    use_case = DownloadReportUseCase(
        db_session=db_session,
        report_job_repo=repo or FakeReportJobRepository(),
    )
    return use_case, db_session


@pytest.mark.unit
class TestDownloadReportUseCase:
    async def test_returns_result_for_completed_pdf_job(self) -> None:
        repo = FakeReportJobRepository()
        job = _make_job(
            status=ReportJobStatus.COMPLETED, file_key="reports/job-001.pdf"
        )
        await repo.save(job)
        use_case, db_session = _build_use_case(repo)

        result = await use_case.execute(DownloadReportCommand(job_id="job-001"))

        assert isinstance(result, DownloadReportResult)
        assert result.file_key == "reports/job-001.pdf"
        assert result.report_format == ReportFormat.PDF
        assert result.report_type == ReportType.SALES_SUMMARY
        assert str(result.date_from) == "2025-01-01"
        assert str(result.date_to) == "2025-12-31"
        db_session.commit.assert_not_called()

    async def test_returns_result_for_completed_csv_job(self) -> None:
        repo = FakeReportJobRepository()
        job = _make_job(
            status=ReportJobStatus.COMPLETED,
            file_key="reports/job-001.csv",
            report_format=ReportFormat.CSV,
        )
        await repo.save(job)
        use_case, _ = _build_use_case(repo)

        result = await use_case.execute(DownloadReportCommand(job_id="job-001"))

        assert result.report_format == ReportFormat.CSV
        assert result.file_key == "reports/job-001.csv"

    async def test_raises_report_job_not_found_when_missing(self) -> None:
        repo = FakeReportJobRepository()
        use_case, _ = _build_use_case(repo)

        with pytest.raises(ReportJobNotFoundError):
            await use_case.execute(DownloadReportCommand(job_id="nonexistent-id"))

    async def test_raises_report_not_ready_when_pending(self) -> None:
        repo = FakeReportJobRepository()
        job = _make_job(status=ReportJobStatus.PENDING, file_key=None)
        await repo.save(job)
        use_case, _ = _build_use_case(repo)

        with pytest.raises(ReportNotReadyError):
            await use_case.execute(DownloadReportCommand(job_id="job-001"))

    async def test_raises_report_not_ready_when_processing(self) -> None:
        repo = FakeReportJobRepository()
        job = _make_job(status=ReportJobStatus.PROCESSING, file_key=None)
        await repo.save(job)
        use_case, _ = _build_use_case(repo)

        with pytest.raises(ReportNotReadyError):
            await use_case.execute(DownloadReportCommand(job_id="job-001"))

    async def test_raises_report_not_ready_when_failed(self) -> None:
        repo = FakeReportJobRepository()
        job = _make_job(status=ReportJobStatus.FAILED, file_key=None)
        await repo.save(job)
        use_case, _ = _build_use_case(repo)

        with pytest.raises(ReportNotReadyError):
            await use_case.execute(DownloadReportCommand(job_id="job-001"))
