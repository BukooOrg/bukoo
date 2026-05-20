from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from app.core.constants import ReportFormat, ReportJobStatus, ReportType


@dataclass
class ReportJobEntity:
    _id: str
    _admin_id: str
    _report_type: ReportType
    _date_from: date
    _date_to: date
    _report_format: ReportFormat
    _status: ReportJobStatus
    _created_at: datetime
    _updated_at: datetime
    _limit: int | None = None
    _file_key: str | None = None
    _error_message: str | None = None
    _completed_at: datetime | None = None
    _deleted_at: datetime | None = None

    # getters
    @property
    def id(self) -> str:
        return self._id

    @property
    def admin_id(self) -> str:
        return self._admin_id

    @property
    def report_type(self) -> ReportType:
        return self._report_type

    @property
    def date_from(self) -> date:
        return self._date_from

    @property
    def date_to(self) -> date:
        return self._date_to

    @property
    def report_format(self) -> ReportFormat:
        return self._report_format

    @property
    def status(self) -> ReportJobStatus:
        return self._status

    @property
    def limit(self) -> int | None:
        return self._limit

    @property
    def file_key(self) -> str | None:
        return self._file_key

    @property
    def error_message(self) -> str | None:
        return self._error_message

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def deleted_at(self) -> datetime | None:
        return self._deleted_at

    # methods
    def mark_processing(self) -> None:
        self._status = ReportJobStatus.PROCESSING
        self._updated_at = datetime.now(UTC)

    def mark_completed(self, file_key: str) -> None:
        self._status = ReportJobStatus.COMPLETED
        self._file_key = file_key
        self._completed_at = datetime.now(UTC)
        self._updated_at = datetime.now(UTC)

    def mark_failed(self, error_message: str) -> None:
        self._status = ReportJobStatus.FAILED
        self._error_message = error_message
        self._updated_at = datetime.now(UTC)
