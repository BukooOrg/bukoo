# Author API Set — View Author Detail Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 6. Author             |
| Use Case     | 2. View Author Detail |
| File Index   | 06_02                 |
| Access Level | 🌐 Public             |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | GET                               |
| URL    | `/api/app/v1/authors/{author_id}` |
| Auth   | None                              |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

| Parameter | Type          | Description                     |
| --------- | ------------- | ------------------------------- |
| author_id | string (UUID) | UUIDv7 identifier of the author |

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
    "id": "01932abc-d000-7000-a000-000000000001",
    "name": "George Orwell",
    "created_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                     |
| ----------- | -------------------- | --------------------------------------------- |
| 404         | AUTHOR_NOT_FOUND     | No author with that ID exists in the database |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure on path parameter |

---

## Procedures

1. **No auth guard** — this is a public endpoint; no `CurrentUser` or `AdminUser` dependency is required.

2. **Input validation** — FastAPI extracts `author_id` from the path as a `str`. No additional Pydantic validation is needed beyond what FastAPI provides automatically.

3. **Existence check** — call `await self._author_repo.find_by_id(author_id)`. The current `AuthorRepositoryImpl.find_by_id` performs `select(AuthorModel).where(AuthorModel.id == author_id)`. If the result is `None`, raise `AuthorNotFoundError(author_id)`, which the exception mapper will translate to HTTP 404 with error code `AUTHOR_NOT_FOUND`.

4. **Return** — build and return `ViewAuthorDetailResult` from the `AuthorEntity` fields. No commit is needed (read-only operation).

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                              |
| -------------- | ------ | ---------------------------------- |
| `AuthorEntity` | Read   | Returns `id`, `name`, `created_at` |

### Repository Methods Required

| Interface           | Method                  | New?          |
| ------------------- | ----------------------- | ------------- |
| `IAuthorRepository` | `find_by_id(author_id)` | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                     |
| ------------------------ | --------------- | -------------------------- |
| `ViewAuthorDetailResult` | Result (output) | `id`, `name`, `created_at` |

### New Domain Exceptions

| Exception Class       | File                              | Inherits          |
| --------------------- | --------------------------------- | ----------------- |
| `AuthorNotFoundError` | `app/domain/exceptions/author.py` | `DomainException` |

### New Error Codes

| Constant           | Value                | Description                   |
| ------------------ | -------------------- | ----------------------------- |
| `AUTHOR_NOT_FOUND` | `"AUTHOR_NOT_FOUND"` | No author found with given ID |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/author/view_author_detail/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` equals the requested `author_id`
- [x] `res.body.data.name` is a non-empty string
- [x] `res.body.data.created_at` is a valid ISO 8601 timestamp
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when `author_id` does not exist → error code `AUTHOR_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_author_detail.py`

**Happy Path:**

- [x] `ViewAuthorDetailUseCase.execute(valid_command)` returns `ViewAuthorDetailResult` with correct `id`, `name`, `created_at`

**Error Cases:**

- [x] Raises `AuthorNotFoundError` when `find_by_id` returns `None`

**Edge Cases:**

- [x] A non-existent UUID (valid format, no DB record) raises `AuthorNotFoundError`

---

## Implementation Checklist

- [x] 1. Domain entity — `AuthorEntity` already exists; no changes needed
- [x] 2. Domain exceptions — create `AuthorNotFoundError` in `app/domain/exceptions/author.py`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface method — `find_by_id` already exists on `IAuthorRepository`
- [x] 4. DTOs — add `ViewAuthorDetailResult` to `app/application/dtos/author_dto.py`
- [x] 5. Use case — `app/application/use_cases/author/view_author_detail.py`
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no changes needed (`find_by_id` is already implemented)
- [x] 9. Exception mapping — add `AuthorNotFoundError → 404 AUTHOR_NOT_FOUND` to `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `AUTHOR_NOT_FOUND` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `ViewAuthorDetailResponse` to `app/presentation/schemas/author_schema.py`
- [x] 12. Route handler — add `GET /{author_id}` to `app/presentation/api/app_api/v1/author_routes.py`
- [x] 13. Wire in `deps.py` — `AuthorRepo` alias already exists; no changes needed
- [x] 14. Alembic migration — not needed (no schema changes)
- [x] 15. Bruno test files — `bruno/author/view_author_detail/` with `folder.bru` + `01_success.bru` + `02_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_view_author_detail.py`
