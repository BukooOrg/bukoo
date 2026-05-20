# Admin — Reports & Analytics — View Report Job Status Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 15. Admin — Reports & Analytics |
| Use Case     | 2. View Report Job Status       |
| File Index   | 15_02                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                               |
| ------ | ----------------------------------- |
| Method | GET                                 |
| URL    | `/api/app/v1/reports/jobs/{job_id}` |
| Auth   | Bearer token (ADMIN role)           |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                  |
| --------- | ------------- | ---------------------------- |
| job_id    | string (UUID) | ID of the report job to poll |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "job_id": "01932abc-1234-7abc-89de-000000000001",
    "status": "completed",
    "created_at": "2026-05-20T12:00:00Z",
    "completed_at": "2026-05-20T12:05:30Z",
    "download_url": "https://minio.local/bukoo/reports/01932abc.pdf?X-Amz-Expires=3600&..."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-20T12:10:00Z"
  }
}
```

`completed_at` and `download_url` are `null` when `status` is `pending`, `processing`, or `failed`.

### Error Responses

| HTTP Status | Error Code           | Condition                                       |
| ----------- | -------------------- | ----------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | Missing, expired, or revoked Bearer token       |
| 403         | PERMISSION_DENIED    | Valid token but caller does not have ADMIN role |
| 404         | REPORT_JOB_NOT_FOUND | No report job exists for the given `job_id`     |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency validates the Bearer token, checks the blocklist, and confirms `role == UserRole.ADMIN`. Raises HTTP 401/403 if invalid.
2. **Use case invocation** — Route handler instantiates `ViewReportJobStatusUseCase` with `report_job_repo` and `storage_svc` dependencies, then calls `execute(ViewReportJobStatusCommand(job_id=path_param))`.
3. **Repo lookup** — Call `await self._report_job_repo.find_by_id(command.job_id)`. Returns `ReportJobEntity | None`.
4. **Not-found guard** — If the result is `None`, raise `ReportJobNotFoundError(command.job_id)`. The exception handler maps this to HTTP 404 with error code `REPORT_JOB_NOT_FOUND`.
5. **Presigned URL generation** — If `job.status == ReportJobStatus.COMPLETED` and `job.file_key` is not `None`, call `await self._storage_svc.get_presigned_url(job.file_key)` to produce a time-limited download URL (default TTL: 3600 s). Otherwise set `download_url = None`.
6. **Return** — Build and return `ViewReportJobStatusResult(job_id=job.id, status=job.status, created_at=job.created_at, completed_at=job.completed_at, download_url=download_url)`. No commit — this is a read-only operation.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                            |
| ----------------- | ------ | -------------------------------- |
| `ReportJobEntity` | Read   | Fetched by `job_id`; no mutation |

### Repository Methods Required

| Interface              | Method               | New?          |
| ---------------------- | -------------------- | ------------- |
| `IReportJobRepository` | `find_by_id(job_id)` | No (existing) |

### New DTOs

| DTO Class                    | Type            | Fields                                                                                                                          |
| ---------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `ViewReportJobStatusCommand` | Command (input) | `job_id: str`                                                                                                                   |
| `ViewReportJobStatusResult`  | Result (output) | `job_id: str`, `status: ReportJobStatus`, `created_at: datetime`, `completed_at: datetime \| None`, `download_url: str \| None` |

### New Domain Exceptions

_(None — `ReportJobNotFoundError` already exists in `app/domain/exceptions/report.py`)_

### New Error Codes

_(None — `REPORT_JOB_NOT_FOUND = "REPORT_JOB_NOT_FOUND"` already exists in `error_codes.py`)_

> **Note:** `ReportJobNotFoundError` is not yet registered in `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`. This must be added as part of this implementation.

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/reports/view_report_job_status/`

**`01_success_pending.bru` — Happy Path (pending job):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"pending"`
- [x] `res.body.data.download_url` is `null`
- [x] `res.body.data.completed_at` is `null`
- [x] `res.body.meta.requestId` is a string

**`02_success_completed.bru` — Happy Path (completed job):**

- [x] Status 200 OK
- [x] `res.body.data.status` equals `"completed"`
- [x] `res.body.data.download_url` is a non-empty string (presigned URL)
- [x] `res.body.data.completed_at` is a non-null ISO datetime string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 for a non-existent `job_id` → error code `REPORT_JOB_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_report_job_status.py`

**Happy Path:**

- [x] `execute(command)` with a PENDING job returns `ViewReportJobStatusResult` with `download_url=None` and `completed_at=None`
- [x] `execute(command)` with a COMPLETED job calls `storage_svc.get_presigned_url(file_key)` and returns result with a non-None `download_url`

**Error Cases:**

- [x] Raises `ReportJobNotFoundError` when `find_by_id` returns `None`

**Edge Cases:**

- [x] A FAILED job returns `status="failed"`, `download_url=None`, `completed_at=None`
- [x] A PROCESSING job returns `status="processing"`, `download_url=None`

---

## Implementation Checklist

- [x] 1. Domain entity — existing (`ReportJobEntity`)
- [x] 2. Domain exceptions — existing (`ReportJobNotFoundError`); add to `EXCEPTION_MAP` in `exception_mapper.py`
- [x] 3. Repository interface method — existing (`find_by_id`)
- [x] 4. DTOs — new `ViewReportJobStatusCommand` and `ViewReportJobStatusResult` in `app/application/dtos/report_job_dtos.py`
- [x] 5. Use case — new `app/application/use_cases/report/view_report_job_status.py`
- [x] 6. ORM model — no change
- [x] 7. Mapper — no change
- [x] 8. Repository implementation — no change
- [x] 9. Exception mapping — add `ReportJobNotFoundError` → HTTP 404 / `REPORT_JOB_NOT_FOUND` to `exception_mapper.py`
- [x] 10. Error codes — existing (`REPORT_JOB_NOT_FOUND`)
- [x] 11. Pydantic schemas — new `ViewReportJobStatusResponse` in `app/presentation/schemas/report_job_schema.py`
- [x] 12. Route handler — add `GET /reports/jobs/{job_id}` to `app/presentation/api/app_api/v1/report_routes.py`
- [x] 13. Wire in `deps.py` — `StorageService` already available; inject alongside existing `ReportJobRepo`
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `folder.bru` + `01_success_pending.bru` and `02_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_view_report_job_status.py`
