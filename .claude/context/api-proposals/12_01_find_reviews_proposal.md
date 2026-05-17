# Review API Set — Find Reviews Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 12. Review      |
| Use Case     | 1. Find Reviews |
| File Index   | 12_01           |
| Access Level | 🌐 Public       |
| Status       | Implemented     |

---

## Endpoint

| Field  | Value                                 |
| ------ | ------------------------------------- |
| Method | GET                                   |
| URL    | `/api/app/v1/books/{book_id}/reviews` |
| Auth   | None                                  |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

| Parameter | Type          | Description                         |
| --------- | ------------- | ----------------------------------- |
| `book_id` | string (UUID) | ID of the book to fetch reviews for |

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
        "created_at": "2026-01-15T10:00:00Z",
        "updated_at": "2026-05-16T10:30:00Z",
        "book": {
          "id": "01932abc-0001-7000-0000-000000000002",
          "title": "The Midnight Library",
          "cover_url": "https://..."
        }
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_items": 42,
      "total_pages": 5
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-17T10:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                               |
| ----------- | -------------------- | ----------------------------------------------------------------------- |
| 404         | BOOK_NOT_FOUND       | No active book with the given `book_id` exists (deleted or deactivated) |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (invalid query params)                      |

---

## Procedures

1. **Input validation** — FastAPI validates path parameter `book_id` and query parameters against `ReviewListQueryRequest`. HTTP 422 is returned automatically on Pydantic validation failure.

2. **Book existence check** — Call `await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter(status="activate"))`. If the result is `None`, raise `BookNotFoundError(cmd.book_id)`. Using `status="activate"` ensures 404 is returned for deleted, deactivated, or non-existent books — consistent with public storefront behavior.

3. **Fetch paginated reviews** — Call `await self._review_repo.find_all(query=cmd.query_params, filters=ReviewFilters(book_id=cmd.book_id, is_hidden=False))`. The repository applies three conditions: `deleted_at IS NULL` (base filter on all `find_all` queries), `book_id = cmd.book_id`, and `hidden_at IS NULL` (the `is_hidden=False` filter). This correctly excludes both customer-soft-deleted and admin-hidden reviews from public view. The `ReviewModel` has a `selectin`-loaded `book` relationship, so each entity already carries `_book` populated.

4. **Return** — Build and return `PaginatedResult[PublicReviewItem]` from the fetched entities. Each item includes the core review fields plus an embedded `book` sub-object (id, title, cover_url). `is_hidden` and `hidden_at` are intentionally omitted from the public response to avoid leaking moderation state.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                                            |
| -------------- | ------ | -------------------------------------------------------------------------------- |
| `ReviewEntity` | Read   | Paginated fetch filtered by `book_id`, `deleted_at IS NULL`, `hidden_at IS NULL` |
| `BookEntity`   | Read   | Existence check; `id`, `title`, `cover_url` projected into each review item      |

### Repository Methods Required

| Interface           | Method                                  | New?          |
| ------------------- | --------------------------------------- | ------------- |
| `IReviewRepository` | `find_all(query, filters)`              | No (existing) |
| `IBookRepository`   | `find_by_id(book_id, BookStatusFilter)` | No (existing) |

### New DTOs

| DTO Class            | Type            | Fields                                                                                                                   |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `FindReviewsCommand` | Command (input) | `book_id: str`, `query_params: QueryParams`                                                                              |
| `PublicReviewItem`   | Result (output) | `id`, `book_id`, `user_id`, `order_item_id`, `rating`, `comment`, `created_at`, `updated_at`, `book: BaseReviewBookItem` |

### New Domain Exceptions

_(None — `BookNotFoundError` is already registered.)_

### New Error Codes

_(None — `BOOK_NOT_FOUND` is already registered in `ErrorCode` and `EXCEPTION_MAP`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/01_find_reviews/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] Each item in `res.body.data.items` has a `book` object with `id`, `title`, `cover_url`
- [x] No item exposes `is_hidden` or `hidden_at` fields
- [x] `res.body.data.pagination.page` equals `1`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_book_not_found.bru` — Status 404 when `book_id` does not exist → error code `BOOK_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_reviews.py`

**Happy Path:**

- [x] `FindReviewsUseCase.execute(valid_command)` returns `PaginatedResult[PublicReviewItem]` with correct field values including embedded `book`
- [x] Hidden reviews (where `hidden_at` is set) are excluded from results
- [x] Soft-deleted reviews (where `deleted_at` is set) are excluded from results

**Error Cases:**

- [x] Raises `BookNotFoundError` when `book_id` does not match any active book

**Edge Cases:**

- [x] Returns empty `items` list when no visible reviews exist for the book
- [x] Pagination returns the correct page slice when `total_items` exceeds `page_size`

---

## Implementation Checklist

- [x] 1. Domain entity — _no changes_
- [x] 2. Domain exceptions — _no changes_
- [x] 3. Repository interfaces — _no changes_ (`IReviewRepository.find_all` and `IBookRepository.find_by_id` already cover all access patterns)
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — add `FindReviewsCommand` and `PublicReviewItem`
- [x] 5. Use case (`app/application/use_cases/review/find_reviews.py`) — new file; export from `__init__.py`
- [x] 6. ORM model — _no changes_
- [x] 7. Mapper — _no changes_
- [x] 8. Repository implementation — _no changes_
- [x] 9. Exception mapping — _no changes_
- [x] 10. Error codes — _no changes_
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — add `ReviewListQueryRequest` (mirrors `AdminReviewListQueryRequest` but without `book_id`, `user_id`, `is_hidden` filters) and `PublicReviewItemResponse` (extends `BaseReviewResponse` with a `book: BaseReviewBookItem` field)
- [x] 12. Route handler (`app/presentation/api/app_api/v1/review_routes.py`) — add a second `APIRouter(prefix="/books")` with `GET /{book_id}/reviews` handler (no auth guard); register this router in `v1/__init__.py`
- [x] 13. Wire in `deps.py` — `BookRepo` already exists; _no changes_
- [x] 14. Alembic migration — _no schema changes_
- [x] 15. Bruno test files (`bruno/review/01_find_reviews/` — `folder.bru` + `01_success.bru` + `02_book_not_found.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_find_reviews.py`)
