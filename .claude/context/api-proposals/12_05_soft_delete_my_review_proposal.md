# Review API Set — Soft Delete Review Proposal

## Overview

| Field        | Value                    |
| ------------ | ------------------------ |
| API Set      | 12. Review               |
| Use Case     | 5. Soft Delete My Review |
| File Index   | 12_05                    |
| Access Level | 👤 Customer              |
| Status       | Implemented              |

---

## Endpoint

| Field  | Value                                      |
| ------ | ------------------------------------------ |
| Method | DELETE                                     |
| URL    | `/api/app/v1/users/me/reviews/{review_id}` |
| Auth   | Bearer token (USER role)                   |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter   | Type          | Description                |
| ----------- | ------------- | -------------------------- |
| `review_id` | string (UUID) | ID of the review to delete |

### Query Parameters

_None_

### Request Body

_None_

---

## Response

### Success Response

**Status:** 204 No Content

_(Empty body — the response envelope middleware passes non-JSON responses through unchanged.)_

### Error Responses

| HTTP Status | Error Code           | Condition                                                  |
| ----------- | -------------------- | ---------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No/invalid/expired Bearer token                            |
| 403         | PERMISSION_DENIED    | Token belongs to ADMIN role (customer-only)                |
| 403         | REVIEW_NOT_OWNED     | Review exists but belongs to a different user              |
| 404         | REVIEW_NOT_FOUND     | No review found for `review_id`                            |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (malformed UUID in path param) |

---

## Procedures

1. **Auth/guard** — `CustomerUser` dependency validates the Bearer token, checks the blocklist via `RedisCacheService`, confirms the user is `ACTIVE` and has `role == UserRole.USER`. Returns the authenticated `UserEntity`. Handled entirely in `deps.py`; the use case receives `user_id: str`.

2. **Existence check** — Call `review_repo.find_by_id(cmd.review_id)`. If the result is `None`, raise `ReviewNotFoundError(cmd.review_id)` → HTTP 404 `REVIEW_NOT_FOUND`.

3. **Ownership check** — Compare `review.user_id` with `cmd.user_id`. If they differ, raise `ReviewNotOwnedError(cmd.review_id)` → HTTP 403 `REVIEW_NOT_OWNED`.

4. **Soft-delete** — Call `review.soft_delete()`, which sets `review._deleted_at = datetime.now(UTC)`.

5. **Persist** — Call `await review_repo.save(review)`. The repository does NOT commit.

6. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.

7. **Return** — Return `DeleteReviewResult()` (empty marker DTO). The route handler returns HTTP 204 with no body.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                              |
| -------------- | ------ | ---------------------------------- |
| `ReviewEntity` | Write  | `soft_delete()` sets `_deleted_at` |

### Repository Methods Required

| Interface           | Method                                          | New?          |
| ------------------- | ----------------------------------------------- | ------------- |
| `IReviewRepository` | `find_by_id(review_id) -> ReviewEntity \| None` | No (existing) |
| `IReviewRepository` | `save(review: ReviewEntity) -> None`            | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                           |
| --------------------- | --------------- | -------------------------------- |
| `DeleteReviewCommand` | Command (input) | `user_id: str`, `review_id: str` |
| `DeleteReviewResult`  | Result (output) | _(empty — signals success)_      |

### New Domain Exceptions

_None — `ReviewNotFoundError` and `ReviewNotOwnedError` already exist in `app/domain/exceptions/review.py`._

### New Error Codes

_None — `REVIEW_NOT_FOUND` and `REVIEW_NOT_OWNED` already exist in `app/application/errors/error_codes.py`._

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/12_review/05_soft_delete_my_review/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 204 No Content
- [x] Response body is empty
- [x] Subsequent `GET /api/app/v1/books/{book_id}/reviews` no longer includes the deleted review

**Error Cases:**

- [x] `02_not_owned.bru` — Status 403 → error code `REVIEW_NOT_OWNED` when review belongs to a different user

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_my_review.py`

**Happy Path:**

- [x] `SoftDeleteMyReviewUseCase.execute(valid_command)` returns `DeleteReviewResult` and calls `review_repo.save()` with a review whose `deleted_at` is not `None`

**Error Cases:**

- [x] Raises `ReviewNotFoundError` when `review_repo.find_by_id` returns `None`
- [x] Raises `ReviewNotOwnedError` when `review.user_id` does not match `cmd.user_id`

**Edge Cases:**

- [x] Raises `ReviewNotFoundError` for soft-deleted review.

---

## Implementation Checklist

- [x] 1. Domain entity — `ReviewEntity` exists; `soft_delete()` method already present — no changes needed
- [x] 2. Domain exceptions — `ReviewNotFoundError`, `ReviewNotOwnedError` already exist — no changes needed
- [x] 3. Repository interface — `find_by_id` and `save` already exist on `IReviewRepository` — no changes needed
- [x] 4. DTOs — add `DeleteReviewCommand` and `DeleteReviewResult` to `app/application/dtos/review_dto.py`
- [x] 5. Use case — `app/application/use_cases/review/soft_delete_my_review.py`
- [x] 6. ORM model — `ReviewModel` exists; no new table
- [x] 7. Mapper — `ReviewMapper` exists; no changes needed
- [x] 8. Repository implementation — no new methods needed on `ReviewRepositoryImpl`
- [x] 9. Exception mapping — `ReviewNotFoundError` and `ReviewNotOwnedError` already in `EXCEPTION_MAP` — no changes needed
- [x] 10. Error codes — `REVIEW_NOT_FOUND` and `REVIEW_NOT_OWNED` already exist — no changes needed
- [x] 11. Pydantic schemas — no request schema needed; route returns HTTP 204 (no response model)
- [x] 12. Route handler — add `DELETE /{review_id}` to `app/presentation/api/app_api/v1/review_routes.py`
- [x] 13. Wire in `deps.py` — `ReviewRepo` and `CustomerUser` already wired — no changes needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/review/05_soft_delete_my_review/` with `folder.bru` + `01_success.bru` + `02_not_owned.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_soft_delete_my_review.py`
