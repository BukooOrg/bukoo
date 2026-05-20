# Admin — Reports & Analytics — Create Report Job Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 15. Admin — Reports & Analytics |
| Use Case     | 1. Create Report Job            |
| File Index   | 15_01                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                      |
| ------ | -------------------------- |
| Method | POST                       |
| URL    | `/api/app/v1/reports/jobs` |
| Auth   | Bearer token (ADMIN role)  |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

### Request Body

| Field       | Type    | Required | Constraints                                                                                     |
| ----------- | ------- | -------- | ----------------------------------------------------------------------------------------------- |
| `type`      | string  | Yes      | One of: `sales_summary`, `top_books`, `top_authors`, `monthly_volume`                           |
| `date_from` | date    | Yes      | ISO 8601 date string; must be strictly before `date_to`                                         |
| `date_to`   | date    | Yes      | ISO 8601 date string; must be strictly after `date_from`                                        |
| `format`    | string  | Yes      | One of: `pdf`, `csv`                                                                            |
| `limit`     | integer | No       | 1–100, default 20. Used only for `top_books` and `top_authors`; ignored for the other two types |

**Example:**

```json
{
  "type": "top_books",
  "date_from": "2025-01-01",
  "date_to": "2025-12-31",
  "format": "pdf",
  "limit": 30
}
```

---

## Response

### Success Response

**Status:** 201 Created

```json
{
  "success": true,
  "data": {
    "job_id": "01932abc-dead-beef-0000-000000000001",
    "status": "pending"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-20T14:32:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                  | Condition                                                                |
| ----------- | --------------------------- | ------------------------------------------------------------------------ |
| 400         | `INVALID_REPORT_DATE_RANGE` | `date_from` is equal to or after `date_to`                               |
| 401         | `AUTH_TOKEN_INVALID`        | Bearer token missing, malformed, or expired                              |
| 403         | `PERMISSION_DENIED`         | Authenticated user does not have `ADMIN` role                            |
| 422         | `UNPROCESSABLE_ENTITY`      | Pydantic validation failure (bad enum, wrong type, `limit` out of range) |

---

## Procedures

### Part A — HTTP Request → Job Persisted → Task Dispatched

1. `AdminUser` dependency in `deps.py` validates the Bearer token and confirms `role == UserRole.ADMIN`. FastAPI raises HTTP 401 if the token is invalid; 403 if the role check fails. The use case is never reached in either case.

2. Pydantic validates the request body against `CreateReportJobRequest`. If `type` or `format` is not a recognised enum value, or `limit` is outside 1–100, FastAPI raises HTTP 422 automatically before the route handler runs.

3. The route handler constructs `CreateReportJobCommand(admin_id=admin.id, report_type=body.type, date_from=body.date_from, date_to=body.date_to, report_format=body.format, limit=body.limit)` and calls `await use_case.execute(command)`.

4. The use case checks `command.date_from >= command.date_to`; if true, raises `InvalidReportDateRangeError`. This maps to HTTP 400 with error code `INVALID_REPORT_DATE_RANGE`.

5. The use case constructs a `ReportJobEntity` with `_id=str(uuid7())`, `_admin_id=command.admin_id`, `_report_type=command.report_type`, `_date_from=command.date_from`, `_date_to=command.date_to`, `_report_format=command.report_format`, `_status=ReportJobStatus.PENDING`, `_limit=command.limit`, `_file_key=None`, `_error_message=None`, `_completed_at=None`, and timestamps set to `datetime.now(UTC)`.

6. The use case calls `await self._report_job_repo.save(job)`. The repository does not commit.

7. The use case calls `await self._db_session.commit()`. The job row is now visible in the database with status `pending`.

8. The use case calls `self._report_job_service.dispatch_report_job(job.id)`. `IReportJobService` is the application-layer interface; the infrastructure implementation `CeleryReportJobService` calls `generate_report.delay(job_id)`, enqueuing the task on the `default` Celery queue.

9. The use case returns `CreateReportJobResult(job_id=job.id, status=job.status)`. The route handler wraps this in `CreateReportJobResponse` and returns HTTP 201.

---

### Part B — Celery Task: `generate_report`

The task is defined in `app/infrastructure/tasks/report_tasks.py`. It is synchronous; all async logic runs inside an `asyncio.run(_run(job_id))` call following the pattern established in `notification_tasks.py`. There are no Celery retries — report failures are deterministic, not transient.

**B.1 — Load and guard**

The inner `_run(job_id)` coroutine opens a fresh DB session via `task_db_session()` (from the new `task_db.py` module, shared with `notification_tasks.py`). It instantiates `ReportJobRepositoryImpl(session)` and calls `find_by_id(job_id)`. If the result is `None` (job deleted before the task ran), the function returns silently.

**B.2 — Transition to `processing` (first commit)**

`job.mark_processing()` sets `_status = ReportJobStatus.PROCESSING` and updates `_updated_at`. `repo.save(job)` is called, then `await session.commit()`. This commit makes the `processing` status immediately visible to any 15.2 poll that arrives while the query is running.

**B.3 — Query report data (inside try/except)**

`_query_report_data(session, job)` dispatches on `job.report_type` to one of four async query functions. All four query functions count only orders with `status IN ('paid', 'shipped', 'delivered')` and `deleted_at IS NULL`, filtered by `created_at::date BETWEEN date_from AND date_to`. The ORM models for `orders`, `order_items`, `books`, `book_authors`, `authors` are queried via SQLAlchemy `select()` with explicit joins:

- **`sales_summary`**: Joins `orders` with `order_items`. Returns one `SalesSummaryData` dataclass: `total_revenue` (sum of `order.total_amount`), `total_orders` (count of distinct order ids), `total_units_sold` (sum of `order_item.quantity`), `total_unique_customers` (count of distinct `order.user_id`), `average_order_value` (computed in Python as `total_revenue / total_orders`, or `Decimal("0")` if no orders).

- **`top_books`**: Joins `order_items → orders → books`. Groups by `book_id`. Aggregates `units_sold` (sum qty) and `revenue` (sum qty × unit_price). Orders by `units_sold DESC`, limited by `job.limit` (defaulting to 20 if `None`). For each returned book, a second query fetches comma-joined author names via `book_authors → authors` and the category name from `books → categories`. Returns a list of `TopBooksRow` dataclasses, each carrying `rank`, `book_id`, `title`, `isbn`, `author_names`, `category_name`, `units_sold`, `revenue`.

- **`top_authors`**: Joins `order_items → orders → book_authors → authors`. Groups by `author_id`. Aggregates `total_units_sold`, `total_revenue`, `titles_sold` (count of distinct `book_id`). Orders by `total_units_sold DESC`, limited by `job.limit`. Returns a list of `TopAuthorsRow` dataclasses.

- **`monthly_volume`**: Queries sum of `total_amount`, count of orders, and sum of `order_item.quantity` grouped by `(EXTRACT(YEAR …), EXTRACT(MONTH …))`. Then `_generate_month_series(date_from, date_to)` generates the complete list of `"YYYY-MM"` strings spanning the period using only stdlib date arithmetic. These two lists are merged in Python: months present in the query result use actual values; months absent are filled with zeros. Returns a list of `MonthlyVolumeRow` dataclasses.

**B.4 — Generate file bytes**

`_render_file(job.report_format, data)` dispatches on `job.report_format`:

- **CSV** (`_render_csv(data)`): Writes to a `BytesIO` buffer via `csv.DictWriter`. Rows are drawn from the dataclass list returned in B.3. If the result set is empty, writes only the header row. Returns the buffer's bytes.

- **PDF** (`_render_pdf(data)`): Uses `reportlab.platypus.SimpleDocTemplate` with A4 page size and standard margins, writing to a `BytesIO` buffer. A custom `_NumberedCanvas` subclass overrides `showPage()` and `save()` to support "Page X of Y" footers across all pages — the two-pass approach required by Platypus. `onFirstPage` and `onLaterPages` canvas callbacks draw a branded page header (report title, period, generation timestamp) and the page-number footer on every page. The main content is a `Table(rows, colWidths=..., repeatRows=1)` — `repeatRows=1` causes the column-header row to re-render at the top of every new page automatically. `TableStyle` applies a dark header row background, alternating light-grey row shading, grid lines, and right-aligned numeric columns. Long cell text is wrapped using `Paragraph` objects with a `ParagraphStyle` — this handles book titles or author names that would otherwise overflow. If `data` contains no rows, a styled "No data available for the selected period." paragraph is rendered instead of the table; the file is still a valid, well-formed PDF. Returns the buffer's bytes.

**B.5 — Upload to MinIO**

Builds `key = f"reports/{job.report_format}/{job.id}.{job.report_format}"`. Calls `await MinIOStorage().upload(key, file_bytes, content_type)` where `content_type` is `"text/csv"` for CSV and `"application/pdf"` for PDF.

**B.6 — Transition to `completed` (second commit)**

`job.mark_completed(file_key=key)` sets `_status = ReportJobStatus.COMPLETED`, `_file_key = key`, `_completed_at = datetime.now(UTC)`, updates `_updated_at`. `repo.save(job)` is called, then `await session.commit()`.

**B.7 — On exception: transition to `failed`**

If any step in B.3–B.5 raises, the `except Exception` handler calls `job.mark_failed(error_message=str(exc))`, sets `_status = ReportJobStatus.FAILED`, saves and commits. The exception is then re-raised so Celery marks the task as `FAILURE` in its result backend (visible in Flower).

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                                   |
| ----------------- | ------ | ------------------------------------------------------- |
| `ReportJobEntity` | Write  | New entity; created by use case; mutated by Celery task |

### New Enums (add to `app/core/constants.py`)

| Enum              | Values                                                        |
| ----------------- | ------------------------------------------------------------- |
| `ReportJobStatus` | `pending`, `processing`, `completed`, `failed`                |
| `ReportType`      | `sales_summary`, `top_books`, `top_authors`, `monthly_volume` |
| `ReportFormat`    | `pdf`, `csv`                                                  |

### Repository Methods Required

| Interface              | Method                       | New?                |
| ---------------------- | ---------------------------- | ------------------- |
| `IReportJobRepository` | `save(job: ReportJobEntity)` | Yes (new interface) |
| `IReportJobRepository` | `find_by_id(job_id: str)`    | Yes                 |

`find_by_id` is used internally by the Celery task (not the use case) but belongs on the same interface.

### New DTOs

| DTO Class                | Type            | Fields                                                                      |
| ------------------------ | --------------- | --------------------------------------------------------------------------- |
| `CreateReportJobCommand` | Command (input) | `admin_id`, `report_type`, `date_from`, `date_to`, `report_format`, `limit` |
| `CreateReportJobResult`  | Result (output) | `job_id`, `status`                                                          |

### New Application-Layer Service Interface

| Interface           | File                                               | Method                                     |
| ------------------- | -------------------------------------------------- | ------------------------------------------ |
| `IReportJobService` | `app/application/interfaces/report_job_service.py` | `dispatch_report_job(job_id: str) -> None` |

Infrastructure implementation: `CeleryReportJobService` in `app/infrastructure/tasks/report_job_service.py` — calls `generate_report.delay(job_id)`.

### New Domain Exceptions

| Exception Class               | File                              | Inherits          |
| ----------------------------- | --------------------------------- | ----------------- |
| `InvalidReportDateRangeError` | `app/domain/exceptions/report.py` | `DomainException` |
| `ReportJobNotFoundError`      | `app/domain/exceptions/report.py` | `DomainException` |

`ReportJobNotFoundError` is defined now (same file) but first mapped and used in 15.2–15.4.

### New Error Codes

| Constant                    | Value                         | Description                                     |
| --------------------------- | ----------------------------- | ----------------------------------------------- |
| `INVALID_REPORT_DATE_RANGE` | `"INVALID_REPORT_DATE_RANGE"` | `date_from` is equal to or after `date_to`      |
| `REPORT_JOB_NOT_FOUND`      | `"REPORT_JOB_NOT_FOUND"`      | Defined now; mapped in exception_mapper in 15.2 |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/15_reports_analytics/01_create_report_job/`

**`01_success_sales_summary.bru` — Happy Path (sales_summary, csv):**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.job_id` is a non-empty string
- [x] `res.body.data.status` equals `"pending"`
- [x] `res.body.meta.requestId` is a string

**`02_success_top_books_pdf.bru` — Happy Path (top_books, pdf, with limit):**

- [x] Status 201 Created
- [x] `res.body.data.status` equals `"pending"`

**Error cases:**

- [x] `02_invalid_date_range_equal.bru` — `date_from == date_to` → Status 400, error code `INVALID_REPORT_DATE_RANGE`
- [x] `03_invalid_date_range_reversed.bru` — `date_from > date_to` → Status 400, error code `INVALID_REPORT_DATE_RANGE`
- [x] `04_invalid_report_type.bru` — Unknown `type` value → Status 422, error code `UNPROCESSABLE_ENTITY`
- [x] `05_limit_out_of_range.bru` — `limit = 0` → Status 422, error code `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_report_job.py`

**Happy Path:**

- [x] `CreateReportJobUseCase.execute(valid_command)` returns `CreateReportJobResult` with a non-empty `job_id` and `status == ReportJobStatus.PENDING`
- [x] `report_job_repo.save()` is called once with the constructed entity
- [x] `report_job_service.dispatch_report_job()` is called once with the entity's `job_id`
- [x] `db_session.commit()` is called once

**Error Cases:**

- [x] Raises `InvalidReportDateRangeError` when `date_from == date_to`
- [x] Raises `InvalidReportDateRangeError` when `date_from > date_to`

**Edge Cases:**

- [x] `limit=None` is stored on the entity without error (default case for `sales_summary`)
- [x] `limit=100` (boundary) is accepted and stored

---

## Implementation Checklist

- [x] 1. New enums in `app/core/constants.py` — `ReportJobStatus`, `ReportType`, `ReportFormat`
- [x] 2. Domain entity `app/domain/entities/report_job_entity.py` — `ReportJobEntity` with `mark_processing()`, `mark_completed()`, `mark_failed()` methods
- [x] 3. Domain exceptions `app/domain/exceptions/report.py` — `InvalidReportDateRangeError`, `ReportJobNotFoundError`; export both from `app/domain/exceptions/__init__.py`
- [x] 4. Repository interface `app/domain/repositories/report_job_repository.py` — `IReportJobRepository` with `save` and `find_by_id`
- [x] 5. Service interface `app/application/interfaces/report_job_service.py` — `IReportJobService.dispatch_report_job()`; export from `app/application/interfaces/__init__.py`
- [x] 6. DTOs `app/application/dtos/report_job_dtos.py` — `CreateReportJobCommand`, `CreateReportJobResult`
- [x] 7. Use case `app/application/use_cases/report/create_report_job.py` — `CreateReportJobUseCase`
- [x] 8. ORM model `app/infrastructure/db/models/report_job_model.py` — `ReportJobModel`; import in `backend/migrations/env.py`
- [x] 9. Mapper `app/infrastructure/db/mappers/report_job_mapper.py` — `ReportJobMapper`
- [x] 10. Repository implementation `app/infrastructure/db/repositories/report_job_repository_impl.py` — `ReportJobRepositoryImpl`
- [x] 11. Refactor `app/infrastructure/tasks/task_db.py` — extract `_task_db_session()` from `notification_tasks.py` into this shared module; update `notification_tasks.py` to import from it
- [x] 12. Celery service implementation `app/infrastructure/tasks/report_job_service.py` — `CeleryReportJobService` implementing `IReportJobService`
- [x] 13. Celery task `app/infrastructure/tasks/report_tasks.py` — `generate_report` task + `_query_report_data`, `_render_csv`, `_render_pdf` helpers + `_NumberedCanvas` class
- [x] 14. Update `app/infrastructure/tasks/celery_app.py` — add `"app.infrastructure.tasks.report_tasks"` to `include`; add `"report.*": {"queue": "default", "routing_key": "default"}` to `TASK_ROUTES`
- [x] 15. Error codes `app/application/errors/error_codes.py` — add `INVALID_REPORT_DATE_RANGE` and `REPORT_JOB_NOT_FOUND`
- [x] 16. Exception mapping `app/presentation/http/exception_mapper.py` — map `InvalidReportDateRangeError` → HTTP 400, `INVALID_REPORT_DATE_RANGE`
- [x] 17. Pydantic schemas `app/presentation/schemas/report_job_schema.py` — `CreateReportJobRequest`, `CreateReportJobResponse`
- [x] 18. Route handler `app/presentation/api/app_api/v1/report_routes.py` — `POST /reports/jobs`; register in `v1/__init__.py`
- [x] 19. Wire in `deps.py` — `ReportJobRepo` and `ReportJobSvc` typed aliases
- [x] 20. Add `reportlab` to `backend/pyproject.toml` dependencies
- [x] 21. Alembic migration — `make migrate msg="add report_jobs table"`
- [x] 22. Bruno tests (`bruno/15_reports_analytics/01_create_report_job/` — `folder.bru` + one `.bru` per test case above)
- [x] 23. Pytest unit tests `backend/tests/unit/test_create_report_job.py`
