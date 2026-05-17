# Review API Set — Find Reviews By Admin Proposal

## Overview

| Field        | Value                    |
| ------------ | ------------------------ |
| API Set      | 12. Review               |
| Use Case     | 6. Find Reviews By Admin |
| File Index   | 12_06                    |
| Access Level | 🔑 Admin                 |
| Status       | Implemented              |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | GET                       |
| URL    | `/api/app/v1/reviews`     |
| Auth   | Bearer token (ADMIN role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter   | Type          | Required | Description                                                      |
| ----------- | ------------- | -------- | ---------------------------------------------------------------- |
| `book_id`   | string (UUID) | No       | Filter reviews for a specific book                               |
| `user_id`   | string (UUID) | No       | Filter reviews written by a specific user                        |
| `is_hidden` | boolean       | No       | `true` = only hidden reviews; `false` = only visible; omit = all |
| `page`      | integer       | No       | Page number (default: 1, min: 1)                                 |
| `page_size` | integer       | No       | Items per page (default: 20, min: 1, max: 100)                   |
| `sort`      | string        | No       | Sort expression, e.g. `-created_at` (desc) or `created_at` (asc) |

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
        "id": "01932abc-0001-7000-0000-000000000001",
        "book_id": "01932abc-0001-7000-0000-000000000002",
        "user_id": "01932abc-0001-7000-0000-000000000003",
        "order_item_id": "01932abc-0001-7000-0000-000000000004",
        "rating": 4,
        "comment": "Great read!",
        "is_hidden": false,
        "hidden_at": null,
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-01-15T10:00:00Z",
        "book": {
          "id": "01932abc-0001-7000-0000-000000000002",
          "title": "The Midnight Library",
          "cover_url": "https://..."
        }
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 1,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-17T10:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                      |
| ----------- | -------------------- | ---------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No or invalid Authorization header             |
| 403         | PERMISSION_DENIED    | Token belongs to a `USER`-role account         |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (malformed params) |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency (from `deps.py`) validates the Bearer token, checks the Redis blocklist, confirms `user.role == UserRole.ADMIN`, and raises HTTP 403 if not an admin.

2. **Input validation** — FastAPI validates query parameters against `ReviewListQueryRequest` (inherits `ListQueryRequest`). Includes `page`, `page_size`, `sort`, `book_id`, `user_id`, and `is_hidden`. HTTP 422 is returned automatically on failure.

3. **Query** — Instantiate `FindReviewsByAdminUseCase` and call `execute(FindReviewsByAdminCommand(...))`. The use case calls `review_repo.find_all(query=cmd.query_params, filters=ReviewFilters(...))`.

4. **Filtering** — The repository applies the following `WHERE` clauses on the `reviews` table:
   - Always: `deleted_at IS NULL` (excludes customer-soft-deleted reviews)
   - If `book_id` is set: `book_id = :book_id`
   - If `user_id` is set: `user_id = :user_id`
   - If `is_hidden = True`: `hidden_at IS NOT NULL`
   - If `is_hidden = False`: `hidden_at IS NULL`
   - If `is_hidden` is omitted: no filter on `hidden_at` (returns both hidden and visible)

5. **Pagination** — The repository executes two queries: a `COUNT(*)` subquery for `total_items`, then the paginated result with `ORDER BY created_at DESC` (default), `.offset(...)`, and `.limit(...)`. Results are wrapped in `PaginatedResult[ReviewEntity]`.

6. **Return** — The use case maps each `ReviewEntity` to `AdminReviewItem` (includes `is_hidden` and `hidden_at`). The route handler maps these to `AdminReviewItemResponse` and wraps in `PaginatedResponse[AdminReviewItemResponse]`.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                        |
| -------------- | ------ | -------------------------------------------- |
| `ReviewEntity` | Read   | No mutation; `is_hidden` property is derived |

### Repository Methods Required

| Interface           | Method                                                                                  | New? |
| ------------------- | --------------------------------------------------------------------------------------- | ---- |
| `IReviewRepository` | `find_all(query: QueryParams, filters: ReviewFilters) -> PaginatedResult[ReviewEntity]` | Yes  |

### New DTOs

| DTO Class                   | Type            | Fields                                                                                                                 |
| --------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `FindReviewsByAdminCommand` | Command (input) | `query_params: QueryParams`, `book_id: str \| None`, `user_id: str \| None`, `is_hidden: bool \| None`                 |
| `AdminReviewItem`           | Result item     | `id`, `book_id`, `user_id`, `order_item_id`, `rating`, `comment`, `is_hidden`, `hidden_at`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — no failure paths beyond standard auth errors.)_

### New Error Codes

_(None — no new domain exception registered.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/06_find_reviews_by_admin/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path (no filters):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] `res.body.data.pagination` has `page`, `page_size`, `total_items`, `total_pages`, `has_next`, `has_prev`
- [x] `res.body.meta.requestId` is a string

**`02_success_filtered_hidden.bru` — Filter `is_hidden=true`:**

- [x] Status 200 OK
- [x] All returned items have `is_hidden = true` and `hidden_at` set to a non-null ISO string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_reviews_by_admin.py`

**Happy Path:**

- [x] Returns all reviews when no filters are applied
- [x] `is_hidden` and `hidden_at` are present on each item in the result

**Filter Cases:**

- [x] `book_id` filter → only reviews for that book are returned
- [x] `user_id` filter → only reviews by that user are returned
- [x] `is_hidden=True` → only hidden reviews are returned
- [x] `is_hidden=False` → only visible reviews are returned

**Edge Cases:**

- [x] Returns empty list when no reviews exist
- [x] `query_params` (page, page_size) are passed through to the repository

---

## Implementation Checklist

- [x] 1. Domain entity — `ReviewEntity` exists; `is_hidden` property and `hidden_at` field already present — no changes needed
- [x] 2. Domain exceptions — no changes needed
- [x] 3. Repository interface (`app/domain/repositories/review_repository.py`) — add `ReviewFilters` dataclass and `find_all` abstract method
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — add `FindReviewsByAdminCommand` and `AdminReviewItem`
- [x] 5. Use case (`app/application/use_cases/review/find_reviews_by_admin.py`) — new file; exported from `__init__.py`
- [x] 6. ORM model — `ReviewModel` exists; no schema change
- [x] 7. Mapper — `ReviewMapper` exists; no changes needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/review_repository_impl.py`) — implement `find_all` with `book_id`, `user_id`, `is_hidden` filters and pagination
- [x] 9. Exception mapping — no changes needed
- [x] 10. Error codes — no changes needed
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — add `ReviewListQueryRequest` and `AdminReviewItemResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/review_routes.py`) — add `GET /reviews` with `AdminUser` guard
- [x] 13. Wire in `deps.py` — `ReviewRepo` and `AdminUser` already wired — no changes needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/review/06_find_reviews_by_admin/` with `folder.bru` + `01_success.bru` + `02_success_filtered_hidden.bru`
- [x] 16. Pytest unit tests (`backend/tests/unit/test_find_reviews_by_admin.py`) — 8 test cases
