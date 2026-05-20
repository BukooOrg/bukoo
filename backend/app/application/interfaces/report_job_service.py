from __future__ import annotations

from abc import ABC, abstractmethod


class IReportJobService(ABC):
    @abstractmethod
    def dispatch_report_job(self, job_id: str) -> None:
        pass
