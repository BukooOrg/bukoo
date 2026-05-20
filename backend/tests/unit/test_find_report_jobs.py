from __future__ import annotations

from datetime import UTC, date, datetime
from typing import override
from unittest.mock import AsyncMock

import pytest

from app.application.dtos.report_job_dtos import (
    FindReportJobsCommand,
    ReportJobListItemResult,
)
from app.application.use_cases.report.find_report_jobs import FindReportJobsUseCase
from app.core.constants import ReportFormat, ReportJobStatus, ReportType
from app.core.query_params import PageParams, PaginatedResult, QueryParams
from app.domain.entities.report_job_entity import ReportJobEntity
from app.domain.repositories.report_job_repository import (
    IReportJobRepository,
    ReportJobFilter,
)

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class FakeReportJobRepository(IReportJobRepository):
    def __init__(self, jobs: list[ReportJobEntity] | None = None) -> None:
        self._store: list[ReportJobEntity] = jobs or []

    @override
    async def save(self, job: ReportJobEntity) -> None:
        self._store.append(job)

    @override
    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        return next((j for j in self._store if j.id == job_id), None)

    @override
    async def find_all(
        self, query: QueryParams, filters: ReportJobFilter
    ) -> PaginatedResult[ReportJobEntity]:
        items = [j for j in self._store if j.deleted_at is None]
        if filters.status is not None:
            items = [j for j in items if j.status == filters.status]
        if filters.report_type is not None:
            items = [j for j in items if j.report_type == filters.report_type]
        total = len(items)
        start = query.page.offset
        end = start + query.page.limit
        return PaginatedResult(
            items=items[start:end],
            total_items=total,
            page=query.page.page,
            page_size=query.page.page_size,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_NOW = datetime(2026, 5, 20, 9, 0, 0, tzinfo=UTC)


def _make_job(
    job_id: str = "job-001",
    status: ReportJobStatus = ReportJobStatus.COMPLETED,
    report_type: ReportType = ReportType.SALES_SUMMARY,
) -> ReportJobEntity:
    return ReportJobEntity(
        _id=job_id,
        _admin_id="admin-001",
        _report_type=report_type,
        _date_from=date(2026, 1, 1),
        _date_to=date(2026, 3, 31),
        _report_format=ReportFormat.CSV,
        _status=status,
        _created_at=_NOW,
        _updated_at=_NOW,
    )


def _make_command(
    page: int = 1,
    page_size: int = 20,
    status: ReportJobStatus | None = None,
    report_type: ReportType | None = None,
) -> FindReportJobsCommand:
    return FindReportJobsCommand(
        query_params=QueryParams(page=PageParams(page=page, page_size=page_size)),
        status=status,
        report_type=report_type,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.unit
class TestFindReportJobsUseCase:
    async def test_returns_paginated_result(self) -> None:
        repo = FakeReportJobRepository([_make_job("job-001"), _make_job("job-002")])
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(_make_command())

        assert isinstance(result, PaginatedResult)
        assert result.total_items == 2
        assert len(result.items) == 2
        assert result.page == 1
        assert result.page_size == 20

    async def test_items_are_correct_dto_type(self) -> None:
        repo = FakeReportJobRepository([_make_job()])
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(_make_command())

        item = result.items[0]
        assert isinstance(item, ReportJobListItemResult)
        assert item.id == "job-001"
        assert item.report_type == ReportType.SALES_SUMMARY
        assert item.status == ReportJobStatus.COMPLETED
        assert item.report_format == ReportFormat.CSV
        assert item.date_from == date(2026, 1, 1)
        assert item.date_to == date(2026, 3, 31)

    async def test_filters_by_status(self) -> None:
        repo = FakeReportJobRepository(
            [
                _make_job("job-001", status=ReportJobStatus.COMPLETED),
                _make_job("job-002", status=ReportJobStatus.PENDING),
                _make_job("job-003", status=ReportJobStatus.COMPLETED),
            ]
        )
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(_make_command(status=ReportJobStatus.COMPLETED))

        assert result.total_items == 2
        assert all(i.status == ReportJobStatus.COMPLETED for i in result.items)

    async def test_filters_by_report_type(self) -> None:
        repo = FakeReportJobRepository(
            [
                _make_job("job-001", report_type=ReportType.SALES_SUMMARY),
                _make_job("job-002", report_type=ReportType.TOP_BOOKS),
                _make_job("job-003", report_type=ReportType.SALES_SUMMARY),
            ]
        )
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(
            _make_command(report_type=ReportType.SALES_SUMMARY)
        )

        assert result.total_items == 2
        assert all(i.report_type == ReportType.SALES_SUMMARY for i in result.items)

    async def test_returns_empty_when_no_jobs_match(self) -> None:
        repo = FakeReportJobRepository(
            [_make_job("job-001", status=ReportJobStatus.PENDING)]
        )
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(_make_command(status=ReportJobStatus.FAILED))

        assert result.total_items == 0
        assert result.items == []

    async def test_pagination_slices_correctly(self) -> None:
        jobs = [_make_job(f"job-{i:03d}") for i in range(7)]
        repo = FakeReportJobRepository(jobs)
        use_case = FindReportJobsUseCase(db_session=AsyncMock(), report_job_repo=repo)

        result = await use_case.execute(_make_command(page=2, page_size=3))

        assert result.total_items == 7
        assert len(result.items) == 3
        assert result.page == 2
        assert result.has_next is True
        assert result.has_prev is True
