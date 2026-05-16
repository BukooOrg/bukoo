# Review API Set — Create Review Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 12. Review       |
| Use Case     | 2. Create Review |
| File Index   | 12_02            |
| Access Level | 👤 Customer      |
| Status       | Implemented      |

---

## Endpoint

| Field  | Value                                 |
| ------ | ------------------------------------- |
| Method | POST                                  |
| URL    | `/api/app/v1/books/{book_id}/reviews` |
| Auth   | Bearer token (USER role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                   |
| --------- | ------------- | ----------------------------- |
| book_id   | string (UUID) | ID of the book being reviewed |

### Query Parameters

_(None)_

### Request Body

| Field         | Type    | Required | Constraints                                                             |
| ------------- | ------- | -------- | ----------------------------------------------------------------------- |
| order_item_id | string  | Yes      | UUID; must reference a DELIVERED order item the user owns for this book |
| rating        | integer | No       | 1–5 inclusive; at least one of rating/comment required                  |
| comment       | string  | No       | max 2000 characters; at least one of rating/comment required            |

**Example:**

```json
{
  "order_item_id": "01932abc-0001-7000-a000-000000000001",
  "rating": 5,
  "comment": "An excellent read, highly recommended."
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
    "id": "01932abc-0002-7000-a000-000000000002",
    "bookId": "01932abc-0003-7000-a000-000000000003",
    "userId": "01932abc-0004-7000-a000-000000000004",
    "orderItemId": "01932abc-0001-7000-a000-000000000001",
    "rating": 5,
    "comment": "An excellent read, highly recommended.",
    "createdAt": "2026-01-15T10:30:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code            | Condition                                                            |
| ----------- | --------------------- | -------------------------------------------------------------------- |
| 400         | VALIDATION_ERROR      | Both `rating` and `comment` are absent, or `rating` is outside 1–5   |
| 401         | AUTH_TOKEN_INVALID    | No Bearer token, token expired, or token revoked                     |
| 403         | REVIEW_NOT_ELIGIBLE   | No DELIVERED order item with matching `order_item_id`/`book_id`/user |
| 404         | BOOK_NOT_FOUND        | `book_id` does not match any active book                             |
| 409         | REVIEW_ALREADY_EXISTS | A review for this `order_item_id` already exists                     |
| 422         | UNPROCESSABLE_ENTITY  | Pydantic validation failure (wrong field types, etc.)                |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token (decodes JWT, checks the Redis blocklist, loads the active `UserEntity`). The route handler receives the resolved `UserEntity` as `current_user`.

2. **Input validation** — Pydantic validates the request body: `order_item_id` (required UUID string), `rating` (optional int), `comment` (optional string). A `model_validator` raises HTTP 400 `VALIDATION_ERROR` if both `rating` and `comment` are `None`, and separately if `rating` is provided but outside the range 1–5.

3. **Book existence check** — Call `book_repo.find_by_id(command.book_id, BookStatusFilter(status="activate"))`. If `None`, raise `BookNotFoundError(command.book_id)` → HTTP 404 `BOOK_NOT_FOUND`.

4. **Eligibility check** — Call `order_repo.find_delivered_order_item(user_id=command.user_id, order_item_id=command.order_item_id, book_id=command.book_id)`. This joins `orders` → `order_items`, filtering on `order.user_id == user_id`, `order.status == OrderStatus.DELIVERED`, `order_item.id == order_item_id`, and `order_item.book_id == book_id`. If `None`, raise `ReviewNotEligibleError(command.order_item_id)` → HTTP 403 `REVIEW_NOT_ELIGIBLE`.

5. **Duplicate check** — Call `review_repo.find_by_order_item_id(command.order_item_id)`. If a `ReviewEntity` is returned (review already exists for that order item), raise `ReviewAlreadyExistsError(command.order_item_id)` → HTTP 409 `REVIEW_ALREADY_EXISTS`.

6. **Construct entity** — Build `ReviewEntity(_id=str(uuid7()), _book_id=command.book_id, _order_item_id=command.order_item_id, _user_id=command.user_id, _rating=command.rating, _comment=command.comment, _created_at=datetime.now(UTC), _updated_at=datetime.now(UTC), _deleted_at=None)`.

7. **Persist** — Call `review_repo.save(review)`. The repository does not commit.

8. **Commit** — `await self._db_session.commit()`.

9. **Return** — Build and return `CreateReviewResult` with all review fields. The route handler wraps it in the response schema; `ResponseFormatterMiddleware` applies the `{success, data, meta}` envelope automatically.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                       |
| -------------- | ------ | ----------------------------------------------------------- |
| `BookEntity`   | Read   | Existence check only                                        |
| `OrderEntity`  | Read   | Verifies DELIVERED status and ownership via order_item join |
| `ReviewEntity` | Write  | Created new                                                 |

### Repository Methods Required

| Interface           | Method                                                                                  | New?                |
| ------------------- | --------------------------------------------------------------------------------------- | ------------------- |
| `IBookRepository`   | `find_by_id(book_id, filters)`                                                          | No (existing)       |
| `IOrderRepository`  | `find_delivered_order_item(user_id, order_item_id, book_id) -> OrderItemEntity \| None` | Yes                 |
| `IReviewRepository` | `save(review: ReviewEntity) -> None`                                                    | Yes (new interface) |
| `IReviewRepository` | `find_by_order_item_id(order_item_id: str) -> ReviewEntity \| None`                     | Yes (new interface) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                       |
| --------------------- | --------------- | -------------------------------------------------------------------------------------------- |
| `CreateReviewCommand` | Command (input) | `user_id`, `book_id`, `order_item_id`, `rating`, `comment`                                   |
| `CreateReviewResult`  | Result (output) | `id`, `book_id`, `user_id`, `order_item_id`, `rating`, `comment`, `created_at`, `updated_at` |

### New Domain Exceptions

| Exception Class            | File                              | Inherits          |
| -------------------------- | --------------------------------- | ----------------- |
| `ReviewNotEligibleError`   | `app/domain/exceptions/review.py` | `DomainException` |
| `ReviewAlreadyExistsError` | `app/domain/exceptions/review.py` | `DomainException` |

### New Error Codes

| Constant                | Value                     | Description                                    |
| ----------------------- | ------------------------- | ---------------------------------------------- |
| `REVIEW_NOT_ELIGIBLE`   | `"REVIEW_NOT_ELIGIBLE"`   | User has no DELIVERED order item for this book |
| `REVIEW_ALREADY_EXISTS` | `"REVIEW_ALREADY_EXISTS"` | A review for this order_item_id already exists |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/02_create_review/`

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.data.rating` equals the submitted value
- [x] `res.body.data.comment` equals the submitted value
- [x] `res.body.meta.requestId` is a string

**Error Cases (one file each, seq increments with filename prefix):**

- [x] `02_book_not_found.bru` — Status 404 when `book_id` does not exist → error code `BOOK_NOT_FOUND`
- [x] `03_not_eligible.bru` — Status 403 when `order_item_id` does not belong to a DELIVERED order for this user/book → error code `REVIEW_NOT_ELIGIBLE`
- [x] `04_already_exists.bru` — Status 409 when a review for this `order_item_id` already exists → error code `REVIEW_ALREADY_EXISTS`
- [x] `05_missing_rating_and_comment.bru` — Status 400 when both `rating` and `comment` are omitted → error code `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_review.py`

**Happy Path:**

- [x] `CreateReviewUseCase.execute(valid_command)` returns `CreateReviewResult` with correct `book_id`, `user_id`, `order_item_id`, `rating`, and `comment`

**Error Cases:**

- [x] Raises `BookNotFoundError` when `book_repo.find_by_id` returns `None`
- [x] Raises `ReviewNotEligibleError` when `order_repo.find_delivered_order_item` returns `None`
- [x] Raises `ReviewAlreadyExistsError` when `review_repo.find_by_order_item_id` returns an existing `ReviewEntity`

**Edge Cases:**

- [x] Review is created successfully with only `rating` provided (no `comment`)
- [x] Review is created successfully with only `comment` provided (no `rating`)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/review_entity.py`) — existing, no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/review.py`) — new file with `ReviewNotEligibleError` and `ReviewAlreadyExistsError`; export from `__init__.py`
- [x] 3. Repository interface — `IReviewRepository` new file at `app/domain/repositories/review_repository.py`; add `find_delivered_order_item()` method to existing `IOrderRepository`
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — new file with `CreateReviewCommand` and `CreateReviewResult`
- [x] 5. Use case (`app/application/use_cases/review/create_review.py`) — new file `CreateReviewUseCase`
- [x] 6. ORM model — `ReviewModel` already existed at `app/infrastructure/db/models/review_model.py`
- [x] 7. Mapper (`app/infrastructure/db/mappers/review_mapper.py`) — `ReviewMapper` already existed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/review_repository_impl.py`) — new `ReviewRepositoryImpl`; added `find_delivered_order_item()` to `OrderRepositoryImpl`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — added `ReviewNotEligibleError` → 403, `ReviewAlreadyExistsError` → 409
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — added `REVIEW_NOT_ELIGIBLE` and `REVIEW_ALREADY_EXISTS`
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — new `CreateReviewRequest` and `CreateReviewResponse`
- [x] 12. Route handler — added `POST /{book_id}/reviews` to `app/presentation/api/app_api/v1/book_routes.py`
- [x] 13. Wire in `deps.py` — added `get_review_repository()` provider and `ReviewRepo` alias
- [x] 14. Alembic migration — skipped; `reviews` table already created in `2026_04_29_0929-34d22fa2a4ee_create_all_tables.py`
- [x] 15. Bruno test files (`bruno/review/02_create_review/` — `folder.bru` + `01_success.bru` + 5 error case files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_create_review.py`)
