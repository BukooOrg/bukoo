from __future__ import annotations

from abc import ABC, abstractmethod

from app.domain.entities.report_job_entity import ReportJobEntity


class IReportJobRepository(ABC):
    @abstractmethod
    async def save(self, job: ReportJobEntity) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        pass
