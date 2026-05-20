from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.constants import ReportFormat, ReportJobStatus, ReportType


@dataclass(frozen=True)
class CreateReportJobCommand:
    admin_id: str
    report_type: ReportType
    date_from: date
    date_to: date
    report_format: ReportFormat
    limit: int | None


@dataclass(frozen=True)
class CreateReportJobResult:
    job_id: str
    status: ReportJobStatus
