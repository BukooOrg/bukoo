from __future__ import annotations

from fastapi import APIRouter

from app.application.dtos.report_job_dtos import CreateReportJobCommand
from app.application.use_cases.report import CreateReportJobUseCase
from app.presentation.dependencies.deps import (
    AdminUser,
    DbSession,
    ReportJobRepo,
    ReportJobSvc,
)
from app.presentation.schemas.report_job_schema import (
    CreateReportJobRequest,
    CreateReportJobResponse,
)

router = APIRouter(prefix="/reports", tags=["report"])


@router.post(
    "/jobs",
    response_model=CreateReportJobResponse,
    status_code=201,
    operation_id="createReportJob",
)
async def create_report_job(
    body: CreateReportJobRequest,
    admin: AdminUser,
    db_session: DbSession,
    report_job_repo: ReportJobRepo,
    report_job_svc: ReportJobSvc,
) -> CreateReportJobResponse:
    use_case = CreateReportJobUseCase(
        db_session=db_session,
        report_job_repo=report_job_repo,
        report_job_svc=report_job_svc,
    )
    result = await use_case.execute(
        CreateReportJobCommand(
            admin_id=admin.id,
            report_type=body.type,
            date_from=body.date_from,
            date_to=body.date_to,
            report_format=body.format,
            limit=body.limit,
        )
    )
    return CreateReportJobResponse(job_id=result.job_id, status=result.status)
