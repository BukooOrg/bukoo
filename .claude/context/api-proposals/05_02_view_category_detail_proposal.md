# Category API Set — View Category Detail Proposal

## Overview

| Field        | Value                   |
| ------------ | ----------------------- |
| API Set      | 5. Category             |
| Use Case     | 2. View Category Detail |
| File Index   | 05_02                   |
| Access Level | 🌐 Public               |
| Status       | Implemented             |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | GET                                    |
| URL    | `/api/app/v1/categories/{category_id}` |
| Auth   | None                                   |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

| Parameter   | Type          | Description                       |
| ----------- | ------------- | --------------------------------- |
| category_id | string (UUID) | UUIDv7 identifier of the category |

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
    "collection_id": "01932abc-d000-7000-a000-000000000002",
    "name": "Literary Fiction",
    "url_slug": "literary-fiction",
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
| 404         | CATEGORY_NOT_FOUND   | No live (non-deleted) category with that ID   |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure on path parameter |

---

## Procedures

1. **No auth guard** — this is a public endpoint; no `CurrentUser` or `AdminUser` dependency is required.

2. **Input validation** — FastAPI extracts `category_id` from the path as a `str`. No additional Pydantic validation is needed beyond what FastAPI provides automatically.

3. **Existence check** — call `await self._category_repo.find_by_id(category_id)`. The repository filters `CategoryModel.deleted_at.is_(None)`, so soft-deleted categories return `None`. If the result is `None`, raise `CategoryNotFoundError(category_id)`, which the exception mapper will translate to HTTP 404 with error code `CATEGORY_NOT_FOUND`.

4. **Return** — build and return `ViewCategoryDetailResult` from the `CategoryEntity` fields. No commit is needed (read-only operation).

---

## Domain Impact

### Entities Involved

| Entity           | Access | Notes                                                 |
| ---------------- | ------ | ----------------------------------------------------- |
| `CategoryEntity` | Read   | Returns id, collection_id, name, url_slug, created_at |

### Repository Methods Required

| Interface             | Method                    | New?          |
| --------------------- | ------------------------- | ------------- |
| `ICategoryRepository` | `find_by_id(category_id)` | No (existing) |

### New DTOs

| DTO Class                  | Type            | Fields                                                  |
| -------------------------- | --------------- | ------------------------------------------------------- |
| `ViewCategoryDetailResult` | Result (output) | `id`, `collection_id`, `name`, `url_slug`, `created_at` |

### New Domain Exceptions

_(None — `CategoryNotFoundError` already exists in `app/domain/exceptions/category.py`)_

### New Error Codes

| Constant             | Value                  | Description                     |
| -------------------- | ---------------------- | ------------------------------- |
| `CATEGORY_NOT_FOUND` | `"CATEGORY_NOT_FOUND"` | No category found with given ID |

_(Check if `CATEGORY_NOT_FOUND` already exists in `app/application/errors/error_codes.py` — add only if absent)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/category/view_category_detail/`

| File               | Scenario                                   |
| ------------------ | ------------------------------------------ |
| `01_success.bru`   | Happy path — valid category_id returns 200 |
| `02_not_found.bru` | Non-existent / soft-deleted ID returns 404 |

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.id` equals the requested category_id
- [ ] `res.body.data.collection_id` is a non-empty string
- [ ] `res.body.data.name` is a non-empty string
- [ ] `res.body.data.url_slug` is a non-empty string
- [ ] `res.body.data.created_at` is a valid ISO 8601 timestamp
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_not_found.bru` — Status 404 when category_id does not exist → error code `CATEGORY_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_category_detail.py`

**Happy Path:**

- [ ] `ViewCategoryDetailUseCase.execute(valid_command)` returns `ViewCategoryDetailResult` with correct `id`, `collection_id`, `name`, `url_slug`, `created_at`

**Error Cases:**

- [ ] Raises `CategoryNotFoundError` when `find_by_id` returns `None`

**Edge Cases:**

- [ ] A soft-deleted category (repo returns `None`) correctly raises `CategoryNotFoundError`

---

## Implementation Checklist

- [x] 1. Domain entity — `CategoryEntity` already exists; no changes needed
- [x] 2. Domain exceptions — `CategoryNotFoundError` already exists; no changes needed
- [x] 3. Repository interface method — `find_by_id` already exists on `ICategoryRepository`
- [x] 4. DTOs — add `ViewCategoryDetailResult` to `app/application/dtos/category_dto.py`
- [x] 5. Use case — `app/application/use_cases/category/view_category_detail.py`
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no changes needed (`find_by_id` is already implemented)
- [x] 9. Exception mapping — verify `CategoryNotFoundError → 404 CATEGORY_NOT_FOUND` exists in `app/presentation/http/exception_mapper.py`; add if absent
- [x] 10. Error codes — verify `CATEGORY_NOT_FOUND` exists in `app/application/errors/error_codes.py`; add if absent
- [x] 11. Pydantic schemas — add `ViewCategoryDetailResponse` to `app/presentation/schemas/category_schema.py`
- [x] 12. Route handler — add `GET /{category_id}` to `app/presentation/api/app_api/v1/category_routes.py`
- [x] 13. Wire in `deps.py` — `CategoryRepo` alias already exists; no changes needed
- [x] 14. Alembic migration — not needed (no schema changes)
- [x] 15. Bruno test files — `bruno/category/view_category_detail/` with `folder.bru` + `01_success.bru` + `02_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_view_category_detail.py`
