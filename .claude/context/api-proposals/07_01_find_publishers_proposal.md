# Publisher API Set — Find Publishers Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 7. Publisher       |
| Use Case     | 1. Find Publishers |
| File Index   | 07_01              |
| Access Level | 🌐 Public          |
| Status       | Approved           |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | GET                      |
| URL    | `/api/app/v1/publishers` |
| Auth   | None                     |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type    | Required | Default | Description                                                                         |
| --------- | ------- | -------- | ------- | ----------------------------------------------------------------------------------- |
| page      | integer | No       | 1       | Page number (≥ 1)                                                                   |
| page_size | integer | No       | 20      | Items per page (1–100)                                                              |
| sort      | string  | No       | —       | Comma-separated sort fields; prefix `-` for descending (e.g. `name`, `-created_at`) |
| search    | string  | No       | —       | Free-text search on publisher name                                                  |

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
        "id": "01932abc-dead-beef-0000-111122223333",
        "name": "Macmillan Publishers",
        "website": "https://www.macmillan.com",
        "created_at": "2026-01-15T10:30:00Z"
      }
    ],
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
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                          |
| ----------- | -------------------- | ------------------------------------------------------------------ |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (e.g. `page` < 1 or `page_size` > 100) |

---

## Procedures

1. **Input validation** — FastAPI resolves `ListQueryRequest` via `Depends(ListQueryRequest)`, which validates `page` (≥ 1) and `page_size` (1–100) automatically. Pydantic returns HTTP 422 on failure; no domain code is reached.
2. **Build query params** — `list_params.to_query_params()` constructs a `QueryParams` object with `PageParams(page, page_size)`, `sorts` (parsed from the `sort` string by `parse_sort()`), and the optional `search` string.
3. **Execute use case** — The route handler instantiates `FindPublishersUseCase(db_session, publisher_repo)` and calls `await use_case.execute(FindPublishersCommand(query=query_params))`.
4. **Repository query** — The use case calls `await self._publisher_repo.find_all(cmd.query)`, which executes a paginated `SELECT` against the `publishers` table filtered by `deleted_at IS NULL`. If `query.search` is set, the query adds a case-insensitive `ILIKE` filter on `name`. Sorting is applied from `query.sorts`; default ordering is `created_at ASC` when no sort is specified. Returns `PaginatedResult[PublisherEntity]`.
5. **Map to result** — The use case maps each `PublisherEntity` to a `BasePublisherResult(id, name, website, created_at)` and returns `PaginatedResult[BasePublisherResult]`.
6. **Return** — The route handler builds a `PaginatedResponse[PublisherListItemResponse]` from the result and returns it. `ResponseFormatterMiddleware` wraps it in the `{success, data, meta}` envelope.

No mutations occur; `commit()` is never called.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                         |
| ----------------- | ------ | --------------------------------------------- |
| `PublisherEntity` | Read   | Fields: `id`, `name`, `website`, `created_at` |

### Repository Methods Required

| Interface              | Method                                                             | New? |
| ---------------------- | ------------------------------------------------------------------ | ---- |
| `IPublisherRepository` | `find_all(query: QueryParams) -> PaginatedResult[PublisherEntity]` | Yes  |

### New DTOs

| DTO Class               | Type            | Fields                                                                 |
| ----------------------- | --------------- | ---------------------------------------------------------------------- |
| `FindPublishersCommand` | Command (input) | `query: QueryParams`                                                   |
| `BasePublisherResult`   | Result (output) | `id: str`, `name: str`, `website: str \| None`, `created_at: datetime` |

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/publisher/find_publishers/`

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.items` is an array
- [ ] Each item has `id`, `name`, `website`, and `created_at` fields
- [ ] `res.body.data.pagination.page` equals 1
- [ ] `res.body.data.pagination.page_size` equals 20
- [ ] `res.body.data.pagination.total_items` is a number
- [ ] `res.body.data.pagination.total_pages` is a number
- [ ] `res.body.data.pagination.has_prev` is `false`
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_sort_descending.bru` — Status 200 with `?sort=-name`; verifies results are returned without error
- [ ] `03_second_page.bru` — Status 200 with `?page=2&page_size=5`; verifies `pagination.page` equals 2
- [ ] `04_search.bru` — Status 200 with `?search=pen`; verifies results returned (may be empty array)
- [ ] `05_invalid_page.bru` — Status 422 when `?page=0` → `UNPROCESSABLE_ENTITY`
- [ ] `06_invalid_page_size.bru` — Status 422 when `?page_size=200` → `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_publishers.py`

**Happy Path:**

- [ ] `FindPublishersUseCase.execute(FindPublishersCommand(query=QueryParams()))` returns `PaginatedResult[BasePublisherResult]` with correct `id`, `name`, `website`, and `created_at` values for each item

**Edge Cases:**

- [ ] Returns empty `items` list when repository returns zero publishers (e.g. `total_items=0`)
- [ ] Returns `PaginatedResult` with correct `page` and `page_size` when non-default pagination is supplied

---

## Implementation Checklist

- [ ] 1. Domain entity (`app/domain/entities/publisher_entity.py`) — existing, no changes needed
- [ ] 2. Domain exceptions (`app/domain/exceptions/publisher.py`) — existing, no new exceptions needed
- [ ] 3. Repository interface method(s) (`app/domain/repositories/publisher_repository.py`) — add `find_all(query: QueryParams) -> PaginatedResult[PublisherEntity]`
- [ ] 4. DTOs (`app/application/dtos/publisher_dto.py`) — add `FindPublishersCommand` and `BasePublisherResult`
- [ ] 5. Use case (`app/application/use_cases/publisher/find_publishers.py`) — new file
- [ ] 6. ORM model — existing (`publisher_model.py`), no changes needed
- [ ] 7. Mapper — existing (`publisher_mapper.py`), no changes needed
- [ ] 8. Repository implementation (`app/infrastructure/db/repositories/publisher_repository_impl.py`) — add `find_all()` implementation
- [ ] 9. Exception mapping — no new exceptions, no changes needed
- [ ] 10. Error codes — no new codes, no changes needed
- [ ] 11. Pydantic schemas (`app/presentation/schemas/publisher_schema.py`) — add `PublisherListItemResponse`
- [ ] 12. Route handler (`app/presentation/api/app_api/v1/publisher_routes.py`) — add `GET /publishers` handler
- [ ] 13. Wire in `deps.py` — add `PublisherRepo` alias if not already present
- [ ] 14. Alembic migration — not needed (no schema changes)
- [ ] 15. Bruno test files (`bruno/publisher/find_publishers/` — `folder.bru` + `01_success.bru` + one file per error/edge case)
- [ ] 16. Pytest unit tests (`backend/tests/unit/test_find_publishers.py`)
