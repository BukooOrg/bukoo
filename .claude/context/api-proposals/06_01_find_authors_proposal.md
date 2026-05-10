# Author API Set — Find Authors Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 6. Author       |
| Use Case     | 1. Find Authors |
| File Index   | 06_01           |
| Access Level | 🌐 Public       |
| Status       | Approved        |

---

## Endpoint

| Field  | Value                 |
| ------ | --------------------- |
| Method | GET                   |
| URL    | `/api/app/v1/authors` |
| Auth   | None                  |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

_None_

### Query Parameters

| Parameter   | Type    | Required | Default | Description                                                                                                                                                                                                            |
| ----------- | ------- | -------- | ------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `sort`      | string  | No       | None    | Sort expression. Comma-separated fields; prefix `-` for descending. e.g. `-created_at,name`. Supported fields: `name`, `created_at`, `updated_at`. Unknown fields silently ignored; default sort is `created_at DESC`. |
| `page`      | integer | No       | `1`     | Page number (≥ 1)                                                                                                                                                                                                      |
| `page_size` | integer | No       | `20`    | Items per page (1 – 100)                                                                                                                                                                                               |

### Request Body

_None_

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
        "id": "01932abc-1234-7abc-abcd-000000000001",
        "name": "Fyodor Dostoevsky",
        "created_at": "2026-01-15T09:00:00Z"
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

When no authors exist or the page exceeds total pages, `items` is `[]` and pagination metadata reflects the actual totals.

### Error Responses

| HTTP Status | Error Code       | Condition                                         |
| ----------- | ---------------- | ------------------------------------------------- |
| 422         | VALIDATION_ERROR | `page < 1`, `page_size < 1`, or `page_size > 100` |

---

## Procedures

1. No authentication is required. The route has no `CurrentUser` or `AdminUser` dependency — the endpoint is fully public.

2. FastAPI resolves `ListQueryRequest` via `Depends(ListQueryRequest)`. Pydantic validates: `page >= 1`, `1 <= page_size <= 100`. If validation fails, FastAPI returns HTTP 422 automatically before the handler is called.

3. The route calls `list_params.to_query_params()`, which invokes `parse_sort(self.sort)` to parse the sort string into a `list[SortOrder]` and constructs `QueryParams(page=PageParams(page=..., page_size=...), sorts=[...])`.

4. The route instantiates `FindAuthorsUseCase` and calls `execute(FindAuthorsCommand(query=query_params))`.

5. `FindAuthorsUseCase.execute()` calls `await self._author_repo.find_all(cmd.query)`.

6. `AuthorRepositoryImpl.find_all()` performs two database queries:
   - **COUNT query:** `SELECT COUNT(*) FROM authors WHERE deleted_at IS NULL` — obtains `total_items`.
   - **ORDER BY:** builds clauses from `query.sorts`, consulting `SORTABLE_FIELDS = {"name": AuthorModel.name, "created_at": AuthorModel.created_at, "updated_at": AuthorModel.updated_at}`. Fields not in the allowlist are silently skipped. If no valid sort fields remain, defaults to `AuthorModel.created_at DESC`.
   - **Data query:** `SELECT * FROM authors WHERE deleted_at IS NULL ORDER BY ... OFFSET ... LIMIT ...` using `query.page.offset` and `query.page.limit`.
   - Returns `PaginatedResult[AuthorEntity]`.

7. `FindAuthorsUseCase` maps each `AuthorEntity` to `BaseAuthorResult(id, name, created_at)` and wraps in a new `PaginatedResult[BaseAuthorResult]` carrying the same `total_items`, `page`, `page_size`.

8. The route maps each `BaseAuthorResult` to `AuthorListItemResponse(id, name, created_at)`, builds `PaginationMeta.from_result(result)`, and returns `PaginatedResponse(items=[...], pagination=...)`. The `ResponseFormatterMiddleware` wraps this in the standard `{ success, data, meta }` envelope.

No `commit()` is called — this is a read-only operation.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                        |
| -------------- | ------ | ---------------------------- |
| `AuthorEntity` | Read   | Queried with pagination/sort |

### Repository Methods Required

| Interface           | Method                                                          | New?                      |
| ------------------- | --------------------------------------------------------------- | ------------------------- |
| `IAuthorRepository` | `find_all(query: QueryParams) -> PaginatedResult[AuthorEntity]` | Yes — already implemented |

### New DTOs

| DTO Class            | Type            | Fields                     |
| -------------------- | --------------- | -------------------------- |
| `FindAuthorsCommand` | Command (input) | `query: QueryParams`       |
| `BaseAuthorResult`   | Result (output) | `id`, `name`, `created_at` |

The use case returns `PaginatedResult[BaseAuthorResult]` directly (no wrapper result class needed).

### New Domain Exceptions

_None — an empty result set returns HTTP 200 with an empty `items` list._

### New Error Codes

_None_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/author/find_authors/`

| File                        | Scenario                                                               |
| --------------------------- | ---------------------------------------------------------------------- |
| `01_success.bru`            | Default call — 200, `items` is a list, `pagination.has_prev` is false  |
| `02_sort_descending.bru`    | `?sort=-name` — verify first item name is alphabetically last          |
| `03_second_page.bru`        | `?page=2&page_size=5` — `pagination.has_prev` is true, `page` equals 2 |
| `04_unknown_sort_field.bru` | `?sort=-bogus` — 200, falls back to default sort (no error)            |
| `05_invalid_page.bru`       | `?page=0` — 422, `VALIDATION_ERROR`                                    |
| `06_invalid_page_size.bru`  | `?page_size=101` — 422, `VALIDATION_ERROR`                             |

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.items` is an array
- [ ] `res.body.data.pagination.page` equals `1`
- [ ] `res.body.data.pagination.page_size` equals `20`
- [ ] `res.body.data.pagination.has_prev` is `false`
- [ ] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_authors.py`

**Happy Path:**

- [x] `FindAuthorsUseCase.execute(FindAuthorsCommand(query=QueryParams()))` returns `PaginatedResult[BaseAuthorResult]` with correct `id`, `name`, `created_at` values
- [x] `total_items` reflects the count returned by the fake repo
- [x] `has_next` is `true` when `page < total_pages`
- [x] `has_prev` is `true` when `page > 1`

**Edge Cases:**

- [x] Empty repository returns `PaginatedResult` with `items=[]`, `total_items=0`, `total_pages=0`, `has_next=False`, `has_prev=False`
- [x] `parse_sort(None)` returns `[]`
- [x] `parse_sort("-created_at,name")` returns `[SortOrder("created_at","desc"), SortOrder("name","asc")]`
- [x] `parse_sort("-")` returns `[]` (empty field name after stripping `-` is skipped)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/author_entity.py`) — existing
- [x] 2. Domain exceptions — none needed
- [x] 3. Repository interface method — `IAuthorRepository.find_all()` added
- [x] 4. DTOs — `FindAuthorsCommand`, `BaseAuthorResult` added to `author_dto.py`
- [x] 5. Use case — `app/application/use_cases/author/find_authors.py`
- [x] 6. ORM model — existing (`AuthorModel`)
- [x] 7. Mapper — existing (`AuthorMapper`)
- [x] 8. Repository implementation — `AuthorRepositoryImpl.find_all()` implemented
- [x] 9. Exception mapping — none needed
- [x] 10. Error codes — none needed
- [x] 11. Pydantic schemas — `AuthorListItemResponse` added; `ListQueryRequest`, `PaginationMeta`, `PaginatedResponse` in `list_schema.py`
- [x] 12. Route handler — `GET /authors` added to `author_routes.py`
- [x] 13. Wired in `deps.py` — `AuthorRepo` already present
- [x] 14. Alembic migration — not needed (no schema change)
- [ ] 15. Bruno test files — `bruno/author/find_authors/` (6 files)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_authors.py`
