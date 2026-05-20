from __future__ import annotations

from datetime import date
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.report_job_dtos import (
    CreateReportJobCommand,
    CreateReportJobResult,
)
from app.application.interfaces.report_job_service import IReportJobService
from app.application.use_cases.report.create_report_job import CreateReportJobUseCase
from app.core.constants import ReportFormat, ReportJobStatus, ReportType
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.exceptions.report import InvalidReportDateRangeError
from app.domain.repositories.report_job_repository import IReportJobRepository

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeReportJobRepository(IReportJobRepository):
    def __init__(self) -> None:
        self._store: dict[str, ReportJobEntity] = {}
        self.saved: ReportJobEntity | None = None

    @override
    async def save(self, job: ReportJobEntity) -> None:
        self._store[job.id] = job
        self.saved = job

    @override
    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        return self._store.get(job_id)


class FakeReportJobService(IReportJobService):
    def __init__(self) -> None:
        self.dispatched_job_ids: list[str] = []

    @override
    def dispatch_report_job(self, job_id: str) -> None:
        self.dispatched_job_ids.append(job_id)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_command(
    date_from: date = date(2025, 1, 1),
    date_to: date = date(2025, 12, 31),
    report_type: ReportType = ReportType.SALES_SUMMARY,
    report_format: ReportFormat = ReportFormat.CSV,
    limit: int | None = None,
) -> CreateReportJobCommand:
    return CreateReportJobCommand(
        admin_id="admin-001",
        report_type=report_type,
        date_from=date_from,
        date_to=date_to,
        report_format=report_format,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestCreateReportJobUseCase:
    async def test_returns_pending_result(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )

        result = await use_case.execute(_make_command())

        assert isinstance(result, CreateReportJobResult)
        assert result.job_id
        assert result.status == ReportJobStatus.PENDING

    async def test_saves_job_to_repo(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )

        result = await use_case.execute(_make_command())

        assert repo.saved is not None
        assert repo.saved.id == result.job_id
        assert repo.saved.status == ReportJobStatus.PENDING
        assert repo.saved.admin_id == "admin-001"

    async def test_dispatches_job_after_commit(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )

        result = await use_case.execute(_make_command())

        db_session.commit.assert_called_once()
        assert len(svc.dispatched_job_ids) == 1
        assert svc.dispatched_job_ids[0] == result.job_id

    async def test_raises_when_date_from_equals_date_to(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )
        cmd = _make_command(date_from=date(2025, 6, 1), date_to=date(2025, 6, 1))

        with pytest.raises(InvalidReportDateRangeError):
            await use_case.execute(cmd)

    async def test_raises_when_date_from_after_date_to(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )
        cmd = _make_command(date_from=date(2025, 12, 31), date_to=date(2025, 1, 1))

        with pytest.raises(InvalidReportDateRangeError):
            await use_case.execute(cmd)

    async def test_limit_none_stored_on_entity(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )

        await use_case.execute(_make_command(limit=None))

        assert repo.saved is not None
        assert repo.saved.limit is None

    async def test_limit_boundary_accepted(self) -> None:
        db_session = AsyncMock()
        repo = FakeReportJobRepository()
        svc = FakeReportJobService()
        use_case = CreateReportJobUseCase(
            db_session=db_session, report_job_repo=repo, report_job_svc=svc
        )

        await use_case.execute(_make_command(limit=100))

        assert repo.saved is not None
        assert repo.saved.limit == 100
