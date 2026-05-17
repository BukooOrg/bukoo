# Review API Set — Find My Reviews Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 12. Review         |
| Use Case     | 3. Find My Reviews |
| File Index   | 12_03              |
| Access Level | 👤 Customer        |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                          |
| ------ | ------------------------------ |
| Method | GET                            |
| URL    | `/api/app/v1/users/me/reviews` |
| Auth   | Bearer token (USER role)       |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | No       | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter   | Type    | Required | Default           | Description                                                               |
| ----------- | ------- | -------- | ----------------- | ------------------------------------------------------------------------- |
| `page`      | integer | No       | 1                 | Page number (1-based)                                                     |
| `page_size` | integer | No       | 10                | Results per page (max 100)                                                |
| `sort`      | string  | No       | `created_at:desc` | Sort field and direction (`created_at:asc\|desc`, `updated_at:asc\|desc`) |

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
        "updated_at": "2026-05-16T10:30:00Z",
        "book": {
          "id": "01932abc-0001-7000-0000-000000000002",
          "title": "The Midnight Library",
          "cover_url": "https://..."
        }
      }
  x],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 5,
      "total_pages": 1
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-17T10:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                               |
| ----------- | -------------------- | ------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No or invalid Authorization header, or token is revoked |
| 403         | PERMISSION_DENIED    | Token belongs to an `ADMIN`-role account                |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (invalid query params)      |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency (from `deps.py`) validates the Bearer token, checks the Redis blocklist, confirms `user.role == UserRole.USER`, and raises HTTP 403 if the caller is an admin. The resolved `UserEntity` is passed to the route handler as `current_user`.

2. **Input validation** — FastAPI validates query parameters against `MyReviewListQueryRequest`. HTTP 422 is returned automatically on validation failure.

3. **Fetch paginated reviews** — Call `await self._review_repo.find_all(query=cmd.query_params, filters=ReviewFilters(user_id=cmd.user_id))`. The repository applies two conditions: `deleted_at IS NULL` (base filter) and `user_id = cmd.user_id`. No `is_hidden` filter is applied — the user's own reviews are returned regardless of moderation state, allowing the UI to inform the user if one of their reviews was hidden.

4. **Return** — Build and return `PaginatedResult[ReviewWithBookItem]` from the fetched entities. Each item includes the core review fields, `is_hidden`, `hidden_at`, and an embedded `book` sub-object.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                          |
| -------------- | ------ | -------------------------------------------------------------- |
| `ReviewEntity` | Read   | Paginated fetch filtered by `user_id` and `deleted_at IS NULL` |

### Repository Methods Required

| Interface           | Method                     | New?          |
| ------------------- | -------------------------- | ------------- |
| `IReviewRepository` | `find_all(query, filters)` | No (existing) |

### New DTOs

| DTO Class              | Type            | Fields                                      |
| ---------------------- | --------------- | ------------------------------------------- |
| `FindMyReviewsCommand` | Command (input) | `user_id: str`, `query_params: QueryParams` |

> **Note:** The result item reuses the existing `ReviewWithBookItem` DTO — it already carries all needed fields (`id`, `book_id`, `user_id`, `order_item_id`, `rating`, `comment`, `is_hidden`, `hidden_at`, `created_at`, `updated_at`, `book: BaseReviewBookItem`).

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/03_find_my_reviews/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] Each item has `is_hidden` and `hidden_at` fields
- [x] Each item has a `book` object with `id`, `title`, `cover_url`
- [x] `res.body.data.pagination.page` equals `1`
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_my_reviews.py`

**Happy Path:**

- [x] `FindMyReviewsUseCase.execute(valid_command)` returns `PaginatedResult[ReviewWithBookItem]` with correct field values including embedded `book`
- [x] Only reviews belonging to `cmd.user_id` are returned
- [x] Both hidden and non-hidden reviews are included

**Error Cases:**

_(None — no domain exceptions are raised by this use case)_

**Edge Cases:**

- [x] Returns empty `items` list when the user has no reviews
- [x] Pagination returns the correct page slice when `total_items` exceeds `page_size`

---

## Implementation Checklist

- [x] 1. Domain entity — _no changes_
- [x] 2. Domain exceptions — _no changes_
- [x] 3. Repository interface — _no changes_ (`IReviewRepository.find_all` already supports `user_id` filter)
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — add `FindMyReviewsCommand`
- [x] 5. Use case (`app/application/use_cases/review/find_my_reviews.py`) — new file; export from `__init__.py`
- [x] 6. ORM model — _no changes_
- [x] 7. Mapper — _no changes_
- [x] 8. Repository implementation — _no changes_
- [x] 9. Exception mapping — _no changes_
- [x] 10. Error codes — _no changes_
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — add `MyReviewListQueryRequest` and `MyReviewItemResponse` (extends `BaseAdminReviewResponse`)
- [x] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `GET /me/reviews` handler using `CustomerUser`
- [x] 13. Wire in `deps.py` — `ReviewRepo` already exists; _no changes_
- [x] 14. Alembic migration — _no schema changes_
- [x] 15. Bruno test files (`bruno/review/03_find_my_reviews/` — `folder.bru` + `01_success.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_find_my_reviews.py`)
