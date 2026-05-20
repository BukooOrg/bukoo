from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from app.core.constants import ReportFormat, ReportJobStatus, ReportType

# commands


@dataclass(frozen=True)
class CreateReportJobCommand:
    admin_id: str
    report_type: ReportType
    date_from: date
    date_to: date
    report_format: ReportFormat
    limit: int | None


@dataclass(frozen=True)
class ViewReportJobStatusCommand:
    job_id: str


@dataclass(frozen=True)
class DownloadReportCommand:
    job_id: str


# results
@dataclass(frozen=True)
class CreateReportJobResult:
    job_id: str
    status: ReportJobStatus


@dataclass(frozen=True)
class ViewReportJobStatusResult:
    job_id: str
    status: ReportJobStatus
    created_at: datetime
    completed_at: datetime | None
    download_url: str | None


@dataclass(frozen=True)
class DownloadReportResult:
    file_key: str
    report_format: ReportFormat
    report_type: ReportType
    date_from: date
    date_to: date
