from __future__ import annotations

from typing import override

from app.application.interfaces.report_job_service import IReportJobService


class CeleryReportJobService(IReportJobService):
    @override
    def dispatch_report_job(self, job_id: str) -> None:
        from app.infrastructure.tasks.report_tasks import generate_report

        generate_report.delay(job_id)
