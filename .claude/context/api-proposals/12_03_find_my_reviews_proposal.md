# Review API Set — Find My Reviews Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 12. Review         |
| Use Case     | 3. Find My Reviews |
| File Index   | 12_03              |
| Access Level | 👤 Customer        |
| Status       | Approved           |

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
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_None_

### Query Parameters

| Parameter | Type    | Required | Default | Description              |
| --------- | ------- | -------- | ------- | ------------------------ |
| `page`    | integer | No       | 1       | Page number (1-based)    |
| `size`    | integer | No       | 20      | Items per page (max 100) |

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
        "id": "01932abc-...",
        "book_id": "01932abc-...",
        "order_item_id": "01932abc-...",
        "rating": 4,
        "comment": "Great read!",
        "book": {
          "id": "01932abc-...",
          "title": "The Great Gatsby",
          "cover_url": "https://..."
        },
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T10:30:00Z"
      }
    ],
    "total": 42,
    "page": 1,
    "size": 20,
    "pages": 3
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                   |
| ----------- | -------------------- | ------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No/invalid/expired Bearer token             |
| 403         | PERMISSION_DENIED    | Token belongs to ADMIN role (customer-only) |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure on query params |

---

## Procedures

1. **Auth/guard** — `CustomerUser` dependency validates the Bearer token, checks the blocklist via `RedisCacheService`, confirms the user is `ACTIVE` and has `role == UserRole.USER`. Returns the authenticated `UserEntity`. This is handled entirely in `deps.py`; the use case receives a `user_id` string.

2. **Pagination input validation** — FastAPI validates `page` (≥ 1) and `size` (1–100) as query parameters via the Pydantic schema. Returns HTTP 422 on failure. The use case receives `page` and `size` as integers.

3. **Fetch paginated reviews** — Call `review_repo.find_by_user_id(user_id=cmd.user_id, page=cmd.page, size=cmd.size)` which returns a `PaginatedResult[ReviewEntity]` containing `items`, `total`, `page`, `size`, and `pages`. Each `ReviewEntity` has its `_book` selectin-loaded (title and cover_url are needed for the response).

4. **Return** — Build and return `FindMyReviewsResult` from the paginated data. No commit (read-only operation).

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                          |
| -------------- | ------ | ---------------------------------------------- |
| `ReviewEntity` | Read   | selectin-loads `_book` for title and cover_url |
| `BookEntity`   | Read   | Accessed via `review._book` (selectin-loaded)  |

### Repository Methods Required

| Interface           | Method                                                                  | New? |
| ------------------- | ----------------------------------------------------------------------- | ---- |
| `IReviewRepository` | `find_by_user_id(user_id, page, size) -> PaginatedResult[ReviewEntity]` | Yes  |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                               |
| ---------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------- |
| `FindMyReviewsCommand` | Command (input) | `user_id: str`, `page: int`, `size: int`                                                                             |
| `ReviewBookSummary`    | Result (output) | `id: str`, `title: str`, `cover_url: str \| None`                                                                    |
| `ReviewListItem`       | Result (output) | `id`, `book_id`, `order_item_id`, `rating`, `comment`, `book: ReviewBookSummary \| None`, `created_at`, `updated_at` |

### New Domain Exceptions

_None_

### New Error Codes

_None_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/12_review/03_find_my_reviews/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.items` is an array
- [ ] `res.body.data.total` is a number
- [ ] `res.body.data.page` equals 1
- [ ] `res.body.data.size` equals 20 (default)
- [ ] Each item has `id`, `book_id`, `rating`, `created_at`
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_invalid_page.bru` — Status 422 when `page=0` (below minimum)
- [ ] `03_invalid_size.bru` — Status 422 when `size=200` (above maximum)

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_my_reviews.py`

**Happy Path:**

- [ ] `FindMyReviewsUseCase.execute(valid_command)` returns `FindMyReviewsResult` with correct `items`, `total`, `page`, `size`, `pages`

**Edge Cases:**

- [ ] Returns empty `items` list and `total=0` when the user has no reviews
- [ ] `pages` is calculated correctly as `ceil(total / size)`
- [ ] Results are ordered by `created_at` descending (most recent first)

---

## Implementation Checklist

- [ ] 1. Domain entity — `ReviewEntity` exists; `BookEntity` loaded via selectin — no changes
- [ ] 2. Domain exceptions — none new
- [ ] 3. Repository interface — add `find_by_user_id` to `IReviewRepository`
- [ ] 4. DTOs — add `FindMyReviewsCommand`, `ReviewBookSummary`, `ReviewListItem`, `FindMyReviewsResult` to `app/application/dtos/review_dto.py`
- [ ] 5. Use case — `app/application/use_cases/review/find_my_reviews.py`
- [ ] 6. ORM model — `ReviewModel` exists; no new table
- [ ] 7. Mapper — `ReviewMapper` exists; confirm it maps `_book`; extend if needed
- [ ] 8. Repository implementation — add `find_by_user_id` to `ReviewRepositoryImpl`
- [ ] 9. Exception mapping — no new exceptions
- [ ] 10. Error codes — no new codes
- [ ] 11. Pydantic schemas — add `FindMyReviewsResponse`, `ReviewListItemResponse` to `app/presentation/schemas/review_schema.py`
- [ ] 12. Route handler — add `GET /users/me/reviews` route (likely to `user_routes.py` or a new `me_routes.py`; confirm against existing route file layout)
- [ ] 13. Wire in `deps.py` — `ReviewRepo` already wired; no changes
- [ ] 14. Alembic migration — not needed (no schema change)
- [ ] 15. Bruno test files — `bruno/12_review/03_find_my_reviews/` with `folder.bru` + test files
- [ ] 16. Pytest unit tests — `backend/tests/unit/test_find_my_reviews.py`
