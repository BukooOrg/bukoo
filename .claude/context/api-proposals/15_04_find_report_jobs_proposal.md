# Admin — Reports & Analytics — Find Report Jobs Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 15. Admin — Reports & Analytics |
| Use Case     | 4. Find Report Jobs             |
| File Index   | 15_04                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                      |
| ------ | -------------------------- |
| Method | GET                        |
| URL    | `/api/app/v1/reports/jobs` |
| Auth   | Bearer token (ADMIN role)  |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter   | Type            | Required | Default | Description                                                          |
| ----------- | --------------- | -------- | ------- | -------------------------------------------------------------------- |
| `page`      | integer         | No       | 1       | Page number (1-based, min 1)                                         |
| `page_size` | integer         | No       | 20      | Items per page (min 1, max 100)                                      |
| `sort`      | string          | No       | —       | Sort expression, e.g. `-created_at` (prefix `-` for descending)      |
| `status`    | ReportJobStatus | No       | —       | Filter by job status: `pending`, `processing`, `completed`, `failed` |
| `type`      | ReportType      | No       | —       | Filter by report type: `sales_summary`, `top_books`, `top_authors`   |

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
    "items": [
      {
        "job_id": "01932abc-d1e2-7000-a000-000000000001",
        "type": "sales_summary",
        "date_from": "2026-01-01",
        "date_to": "2026-03-31",
        "format": "pdf",
        "limit": null,
        "status": "completed",
        "created_at": "2026-05-20T09:00:00Z",
        "completed_at": "2026-05-20T09:01:23Z"
      }
  x],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 42,
      "total_pages": 3,
      "has_next": true,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-20T09:05:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                                              |
| ----------- | -------------------- | -------------------------------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | Bearer token missing, expired, or revoked                                              |
| 403         | PERMISSION_DENIED    | Token is valid but role is not ADMIN                                                   |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (invalid enum value for `status`/`type`, `page` < 1, etc.) |

---

## Procedures

1. **Auth/guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the blocklist via `RedisCacheService`, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. A 403 is raised if the role check fails. The use case receives no user identity — this endpoint returns all admins' jobs.

2. **Input validation** — FastAPI + Pydantic parse and validate `FindReportJobsQueryRequest` via `Annotated[FindReportJobsQueryRequest, Depends()]`. Invalid enum values for `status` or `type`, or out-of-range pagination fields, produce an automatic HTTP 422.

3. **Build command** — The route handler constructs a `FindReportJobsCommand` by calling `query.to_query_params()` (inherited from `ListQueryRequest`) to produce a `QueryParams` object, and passes the filter fields directly: `status=query.status`, `report_type=query.type`.

4. **Paginated query** — The use case calls `await self._report_job_repo.find_all(query=cmd.query_params, status=cmd.status, report_type=cmd.report_type)`, which returns `PaginatedResult[ReportJobEntity]`. Results are ordered by `created_at` descending by default (when no `sort` is specified). Soft-deleted jobs are excluded.

5. **Build result** — The use case maps each `ReportJobEntity` to a `ReportJobListItemResult` and returns `PaginatedResult[ReportJobListItemResult]`.

6. **Return** — The route handler builds `PaginatedResponse[ReportJobListItemResponse]` using `items=[...]` and `pagination=PaginationMeta.from_result(result)`, and returns it. `ResponseFormatterMiddleware` wraps it in the `{success, data, meta}` envelope.

No mutations occur; `commit()` is not called.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                 |
| ----------------- | ------ | ------------------------------------- |
| `ReportJobEntity` | Read   | Existing entity; no new fields needed |

### Repository Methods Required

| Interface              | Method                                                                                                                               | New? |
| ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ---- |
| `IReportJobRepository` | `find_all(query: QueryParams, status: ReportJobStatus \| None, report_type: ReportType \| None) -> PaginatedResult[ReportJobEntity]` | Yes  |

### New DTOs

| DTO Class                 | Type            | Fields                                                                                                            |
| ------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------- |
| `FindReportJobsCommand`   | Command (input) | `query_params: QueryParams`, `status: ReportJobStatus \| None`, `report_type: ReportType \| None`                 |
| `ReportJobListItemResult` | Result (output) | `job_id`, `report_type`, `date_from`, `date_to`, `report_format`, `limit`, `status`, `created_at`, `completed_at` |

Use case return type: `PaginatedResult[ReportJobListItemResult]` (existing generic from `app.core.query_params`).

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/reports/04_find_report_jobs/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] `res.body.data.pagination.total_items` is an integer
- [x] `res.body.data.pagination.page` equals 1
- [x] `res.body.data.pagination.page_size` equals 20
- [x] `res.body.data.pagination.has_prev` is `false`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_invalid_status_filter.bru` — Status 422 when `status` query param is an unrecognized value

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_report_jobs.py`

**Happy Path:**

- [x] `FindReportJobsUseCase.execute(valid_command)` returns `PaginatedResult[ReportJobListItemResult]` with correct `items`, `total_items`, `page`, `page_size`

**Filter Cases:**

- [x] Returns only jobs matching the given `status` when `status` filter is applied
- [x] Returns only jobs matching the given `report_type` when `type` filter is applied
- [x] Returns empty `items` and `total_items == 0` when no jobs match the filter

**Pagination:**

- [x] Returns correct page slice and sets `has_next=True` when more pages exist

---

## Implementation Checklist

- [x] 1. Domain entity — existing `ReportJobEntity`, no changes
- [x] 2. Domain exceptions — none needed
- [x] 3. Repository interface — add `find_all(...)` to `IReportJobRepository` in `app/domain/repositories/report_job_repository.py`
- [x] 4. DTOs — add `FindReportJobsCommand` and `ReportJobListItemResult` to `app/application/dtos/report_job_dtos.py`
- [x] 5. Use case — `app/application/use_cases/report/find_report_jobs.py`
- [x] 6. ORM model — existing `ReportJobModel`, no changes
- [x] 7. Mapper — existing `ReportJobMapper`, no changes
- [x] 8. Repository implementation — add `find_all(...)` to `ReportJobRepositoryImpl` in `app/infrastructure/db/repositories/report_job_repository_impl.py`
- [x] 9. Exception mapping — none needed
- [x] 10. Error codes — none needed
- [x] 11. Pydantic schemas — add `FindReportJobsQueryRequest(ListQueryRequest)` and `ReportJobListItemResponse` to `app/presentation/schemas/report_job_schema.py`
- [x] 12. Route handler — add `GET /jobs` handler to `app/presentation/api/app_api/v1/report_routes.py` returning `PaginatedResponse[ReportJobListItemResponse]`
- [x] 13. Wire in `deps.py` — no new dependencies; `ReportJobRepo` alias already exists
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/reports/04_find_report_jobs/` — `folder.bru` + `01_success.bru` + one file per error case
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_report_jobs.py`
