from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from app.core.constants import ReportJobStatus, ReportType
from app.core.query_params import PaginatedResult, QueryParams
from app.domain.entities.report_job_entity import ReportJobEntity


@dataclass(frozen=True)
class ReportJobFilter:
    status: ReportJobStatus | None = None
    report_type: ReportType | None = None


class IReportJobRepository(ABC):
    @abstractmethod
    async def save(self, job: ReportJobEntity) -> None:
        pass

    @abstractmethod
    async def find_by_id(self, job_id: str) -> ReportJobEntity | None:
        pass

    @abstractmethod
    async def find_all(
        self, query: QueryParams, filters: ReportJobFilter
    ) -> PaginatedResult[ReportJobEntity]:
        pass
