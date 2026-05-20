# Admin — Reports & Analytics — Download Report Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 15. Admin — Reports & Analytics |
| Use Case     | 3. Download Report              |
| File Index   | 15_03                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                                        |
| ------ | -------------------------------------------- |
| Method | GET                                          |
| URL    | `/api/app/v1/reports/jobs/{job_id}/download` |
| Auth   | Bearer token (ADMIN role)                    |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description          |
| --------- | ------------- | -------------------- |
| `job_id`  | string (UUID) | ID of the report job |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 200 OK

```
Content-Type: application/pdf   (or text/csv for CSV format)
Content-Disposition: attachment; filename="report_sales_summary_2026-01-01_2026-01-31.pdf"

<file content streamed in 8 MB chunks>
```

This is a binary/text stream — **not** wrapped in the `{success, data, meta}` envelope. `ResponseFormatterMiddleware` passes non-JSON responses through unchanged. `StreamingResponse` from Starlette is returned directly from the route handler.

The filename pattern is: `report_{report_type}_{date_from}_{date_to}.{format}` — e.g. `report_top_books_2026-01-01_2026-03-31.csv`.

### Error Responses

| HTTP Status | Error Code             | Condition                                                                |
| ----------- | ---------------------- | ------------------------------------------------------------------------ |
| 401         | `UNAUTHORIZED`         | No Authorization header                                                  |
| 401         | `TOKEN_EXPIRED`        | Bearer token is expired                                                  |
| 401         | `INVALID_TOKEN`        | Bearer token is malformed or invalid                                     |
| 403         | `ADMIN_ROLE_REQUIRED`  | Authenticated user does not have `ADMIN` role                            |
| 404         | `REPORT_JOB_NOT_FOUND` | No report job exists with the given `job_id`                             |
| 404         | `REPORT_NOT_READY`     | Job exists but status is not `completed` (pending / processing / failed) |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and asserts `role == UserRole.ADMIN`. Raises HTTP 401/403 directly if guard fails — no use case involvement.

2. **Existence check** — `DownloadReportUseCase.execute()` calls `report_job_repo.find_by_id(command.job_id)`. If `None`, raise `ReportJobNotFoundError(command.job_id)` → maps to HTTP 404 `REPORT_JOB_NOT_FOUND`.

3. **Readiness check** — If `job.status != ReportJobStatus.COMPLETED`, raise `ReportNotReadyError(command.job_id)` → maps to HTTP 404 `REPORT_NOT_READY`. (A job may be in `pending`, `processing`, or `failed` status.)

4. **Return result** — Return `DownloadReportResult(file_key=job.file_key, report_format=job.report_format, report_type=job.report_type, date_from=job.date_from, date_to=job.date_to)`. No `commit()` — this is a read-only use case.

5. **Route handler: derive headers** — Determine `content_type` from `result.report_format`: `"application/pdf"` for `ReportFormat.PDF`, `"text/csv"` for `ReportFormat.CSV`. Build `filename` as `f"report_{result.report_type}_{result.date_from}_{result.date_to}.{result.report_format}"`.

6. **Route handler: stream** — Return `StreamingResponse(storage_svc.load_stream(result.file_key), media_type=content_type, headers={"Content-Disposition": f'attachment; filename="{filename}"'})`. `load_stream` yields the object in 8 MB chunks via the `IStorageService` abstraction (MinIO in dev, S3 in prod).

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                                                        |
| ----------------- | ------ | ---------------------------------------------------------------------------- |
| `ReportJobEntity` | Read   | `status`, `file_key`, `report_format`, `report_type`, `date_from`, `date_to` |

### Repository Methods Required

| Interface              | Method           | New?          |
| ---------------------- | ---------------- | ------------- |
| `IReportJobRepository` | `find_by_id(id)` | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                                                                                                        |
| ----------------------- | --------------- | ------------------------------------------------------------------------------------------------------------- |
| `DownloadReportCommand` | Command (input) | `job_id: str`                                                                                                 |
| `DownloadReportResult`  | Result (output) | `file_key: str`, `report_format: ReportFormat`, `report_type: ReportType`, `date_from: date`, `date_to: date` |

### New Domain Exceptions

| Exception Class       | File                              | Inherits          |
| --------------------- | --------------------------------- | ----------------- |
| `ReportNotReadyError` | `app/domain/exceptions/report.py` | `DomainException` |

### New Error Codes

| Constant           | Value                | Description                                           |
| ------------------ | -------------------- | ----------------------------------------------------- |
| `REPORT_NOT_READY` | `"REPORT_NOT_READY"` | Job exists but has not yet reached `completed` status |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/reports/03_download_report/`

- **`01_success_pdf.bru`** — Happy path (PDF): status 200, `Content-Type: application/pdf`, `Content-Disposition` contains `.pdf`
- **`02_success_csv.bru`** — Happy path (CSV): status 200, `Content-Type: text/csv`, `Content-Disposition` contains `.csv`
- **`03_not_found.bru`** — Status 404, error code `REPORT_JOB_NOT_FOUND` when `job_id` does not exist
- **`04_not_ready.bru`** — Status 404, error code `REPORT_NOT_READY` when job status is `pending` or `processing`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_download_report.py`

**Happy Path:**

- [x] `DownloadReportUseCase.execute(valid_command)` returns `DownloadReportResult` with correct `file_key`, `report_format`, `report_type`, `date_from`, `date_to`

**Error Cases:**

- [x] Raises `ReportJobNotFoundError` when `find_by_id` returns `None`
- [x] Raises `ReportNotReadyError` when job status is `ReportJobStatus.PENDING`
- [x] Raises `ReportNotReadyError` when job status is `ReportJobStatus.PROCESSING`
- [x] Raises `ReportNotReadyError` when job status is `ReportJobStatus.FAILED`

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/`) — _existing_ `ReportJobEntity`
- [x] 2. Domain exceptions (`app/domain/exceptions/report.py`) — **new** `ReportNotReadyError`; export from `__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/`) — _existing_ `find_by_id`
- [x] 4. DTOs (`app/application/dtos/report_job_dtos.py`) — **new** `DownloadReportCommand`, `DownloadReportResult`
- [x] 5. Use case (`app/application/use_cases/report/download_report.py`) — **new** `DownloadReportUseCase`; export from `report/__init__.py`
- [x] 6. ORM model — _no change_
- [x] 7. Mapper — _no change_
- [x] 8. Repository implementation — _no change_
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — **new** `ReportNotReadyError → 404 REPORT_NOT_READY`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — **new** `REPORT_NOT_READY`
- [x] 11. Pydantic schemas — _none_ (streaming response, no JSON response model)
- [x] 12. Route handler (`app/presentation/api/app_api/v1/report_routes.py`) — **new** `GET /jobs/{job_id}/download` route returning `StreamingResponse`
- [x] 13. Wire in `deps.py` — _no new deps_ (`ReportJobRepo` and `StorageService` are already wired)
- [x] 14. Alembic migration — _none_ (no schema change)
- [x] 15. Bruno test files (`bruno/reports/03_download_report/` — `folder.bru` + 4 test files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_download_report.py`)
