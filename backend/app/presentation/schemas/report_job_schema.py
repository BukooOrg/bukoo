from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field

from app.core.constants import ReportFormat, ReportJobStatus, ReportType


# requests
class CreateReportJobRequest(BaseModel):
    type: ReportType
    date_from: date
    date_to: date
    format: ReportFormat
    limit: int | None = Field(default=None, ge=1, le=100)


# responses
class CreateReportJobResponse(BaseModel):
    job_id: str
    status: ReportJobStatus
