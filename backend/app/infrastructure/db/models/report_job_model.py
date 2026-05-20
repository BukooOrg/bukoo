from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.constants import ReportFormat, ReportJobStatus, ReportType

from .base import DefaultFieldMixin, SoftDeleteMixin
from .types import EnumText


class ReportJobModel(DefaultFieldMixin, SoftDeleteMixin):
    __tablename__ = "report_jobs"
    __table_args__ = (
        Index("idx_report_jobs_admin_id", "admin_id"),
        Index("idx_report_jobs_status", "status"),
    )

    admin_id: Mapped[str] = mapped_column(String(255), nullable=False)
    report_type: Mapped[ReportType] = mapped_column(
        EnumText(ReportType, length=50), nullable=False
    )
    date_from: Mapped[date] = mapped_column(Date(), nullable=False)
    date_to: Mapped[date] = mapped_column(Date(), nullable=False)
    report_format: Mapped[ReportFormat] = mapped_column(
        EnumText(ReportFormat, length=10), nullable=False
    )
    status: Mapped[ReportJobStatus] = mapped_column(
        EnumText(ReportJobStatus, length=20),
        nullable=False,
        default=ReportJobStatus.PENDING,
    )
    limit: Mapped[int | None] = mapped_column(
        Integer(), nullable=True, default=None, init=False
    )
    file_key: Mapped[str | None] = mapped_column(
        String(500), nullable=True, default=None, init=False
    )
    error_message: Mapped[str | None] = mapped_column(
        Text(), nullable=True, default=None, init=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None, init=False
    )
