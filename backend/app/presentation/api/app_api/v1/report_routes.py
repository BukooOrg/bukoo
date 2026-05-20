from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from starlette.responses import StreamingResponse

from app.application.dtos.report_job_dtos import (
    CreateReportJobCommand,
    DownloadReportCommand,
    FindReportJobsCommand,
    ViewReportJobStatusCommand,
)
from app.application.use_cases.report import (
    CreateReportJobUseCase,
    DownloadReportUseCase,
    FindReportJobsUseCase,
    ViewReportJobStatusUseCase,
)
from app.core.constants import ReportFormat
from app.core.query_params import PageParams, QueryParams, parse_sort
from app.presentation.dependencies.deps import (
    AdminUser,
    DbSession,
    ReportJobRepo,
    ReportJobSvc,
    StorageService,
)
from app.presentation.schemas.list_schema import (
    PaginatedResponse,
    PaginationMeta,
)
from app.presentation.schemas.report_job_schema import (
    CreateReportJobRequest,
    CreateReportJobResponse,
    FindReportJobsQueryRequest,
    ReportJobListItemResponse,
    ViewReportJobStatusResponse,
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


@router.get(
    "/jobs/{job_id}",
    response_model=ViewReportJobStatusResponse,
    status_code=200,
    operation_id="viewReportJobStatus",
)
async def view_report_job_status(
    job_id: str,
    admin: AdminUser,
    db_session: DbSession,
    report_job_repo: ReportJobRepo,
    storage_svc: StorageService,
) -> ViewReportJobStatusResponse:
    use_case = ViewReportJobStatusUseCase(
        db_session=db_session,
        report_job_repo=report_job_repo,
        storage_svc=storage_svc,
    )
    result = await use_case.execute(ViewReportJobStatusCommand(job_id=job_id))
    return ViewReportJobStatusResponse(
        job_id=result.job_id,
        status=result.status,
        created_at=result.created_at,
        completed_at=result.completed_at,
        download_url=result.download_url,
    )


@router.get(
    "/jobs/{job_id}/download",
    status_code=200,
    operation_id="downloadReport",
)
async def download_report(
    job_id: str,
    admin: AdminUser,
    db_session: DbSession,
    report_job_repo: ReportJobRepo,
    storage_svc: StorageService,
) -> StreamingResponse:
    use_case = DownloadReportUseCase(
        db_session=db_session,
        report_job_repo=report_job_repo,
    )
    result = await use_case.execute(DownloadReportCommand(job_id=job_id))

    content_type = (
        "application/pdf" if result.report_format == ReportFormat.PDF else "text/csv"
    )
    filename = (
        f"report_{result.report_type}_{result.date_from}_{result.date_to}"
        f".{result.report_format}"
    )
    return StreamingResponse(
        storage_svc.load_stream(result.file_key),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get(
    "/jobs",
    response_model=PaginatedResponse[ReportJobListItemResponse],
    status_code=200,
    operation_id="findReportJobs",
)
async def find_report_jobs(
    admin: AdminUser,
    db_session: DbSession,
    report_job_repo: ReportJobRepo,
    query: Annotated[FindReportJobsQueryRequest, Depends()],
) -> PaginatedResponse[ReportJobListItemResponse]:
    cmd = FindReportJobsCommand(
        query_params=QueryParams(
            page=PageParams(page=query.page, page_size=query.page_size),
            sorts=parse_sort(query.sort),
        ),
        status=query.status,
        report_type=query.type,
    )
    use_case = FindReportJobsUseCase(
        db_session=db_session,
        report_job_repo=report_job_repo,
    )
    result = await use_case.execute(cmd)
    return PaginatedResponse(
        items=[
            ReportJobListItemResponse(
                job_id=item.id,
                type=item.report_type,
                date_from=item.date_from,
                date_to=item.date_to,
                format=item.report_format,
                limit=item.limit,
                status=item.status,
                created_at=item.created_at,
                completed_at=item.completed_at,
            )
            for item in result.items
        ],
        pagination=PaginationMeta.from_result(result),
    )
