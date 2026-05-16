# Review API Set — Update Review Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 12. Review       |
| Use Case     | 4. Update Review |
| File Index   | 12_04            |
| Access Level | 👤 Customer      |
| Status       | Implemented      |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | PATCH                             |
| URL    | `/api/app/v1/reviews/{review_id}` |
| Auth   | Bearer token (USER role)          |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                |
| --------- | ------------- | -------------------------- |
| review_id | string (UUID) | ID of the review to update |

### Query Parameters

_(None)_

### Request Body

| Field   | Type          | Required | Constraints                                  |
| ------- | ------------- | -------- | -------------------------------------------- |
| rating  | integer\|null | No       | 1–5 inclusive; null clears the rating        |
| comment | string\|null  | No       | max 2000 characters; null clears the comment |

At least one of `rating` or `comment` must be explicitly present in the body (validated via `model_fields_set`).

**Example:**

```json
{
  "rating": 4,
  "comment": "Updated my thoughts — still a great read."
}
```

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "01932abc-dead-beef-0000-000000000001",
    "book_id": "01932abc-dead-beef-0000-000000000002",
    "user_id": "01932abc-dead-beef-0000-000000000003",
    "order_item_id": "01932abc-dead-beef-0000-000000000004",
    "rating": 4,
    "comment": "Updated my thoughts — still a great read.",
    "created_at": "2026-01-10T08:00:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                  |
| ----------- | -------------------- | ---------------------------------------------------------- |
| 400         | VALIDATION_ERROR     | Body provides neither `rating` nor `comment`               |
| 401         | AUTH_TOKEN_INVALID   | Missing, expired, or revoked Bearer token                  |
| 403         | REVIEW_NOT_OWNED     | Authenticated user does not own the review                 |
| 404         | REVIEW_NOT_FOUND     | No non-deleted review exists with the given `review_id`    |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (e.g. rating out of 1–5 range) |

---

## Procedures

1. **Auth guard** — The `CurrentUser` dependency in `deps.py` decodes the Bearer token via `JWTService`, checks the blocklist in `RedisCacheService`, and resolves the active `UserEntity`. Returns HTTP 401 if the token is invalid, expired, or revoked.

2. **Input validation** — FastAPI/Pydantic validates `UpdateReviewRequest`. A `model_validator(mode="after")` inspects `model_fields_set`; if neither `"rating"` nor `"comment"` is present in `model_fields_set`, it raises `ValueError` → HTTP 400 `VALIDATION_ERROR`. Field-level constraints (rating 1–5, comment max 2000 chars) are enforced by Pydantic field validators → HTTP 422 on failure.

3. **Fetch review** — `UpdateReviewUseCase.execute(cmd)` calls `await self._review_repo.find_by_id(cmd.review_id)`. If `None`, raise `ReviewNotFoundError(cmd.review_id)` → HTTP 404 `REVIEW_NOT_FOUND`.

4. **Ownership check** — If `review.user_id != cmd.user_id`, raise `ReviewNotOwnedError(cmd.review_id)` → HTTP 403 `REVIEW_NOT_OWNED`.

5. **Merge updated values** — Compute the final rating and comment by merging the command fields against the existing review: only fields explicitly present in `cmd.fields_to_update` are replaced; all others retain the review's current value.

   ```python
   new_rating  = cmd.rating  if "rating"  in cmd.fields_to_update else review.rating
   new_comment = cmd.comment if "comment" in cmd.fields_to_update else review.comment
   ```

6. **Domain rule enforcement** — Both `new_rating` and `new_comment` may both be `None` only if the opposite field is non-None. (This invariant is guaranteed by the request validator in step 2 — after merging, at least one field will remain set unless the user's prior review had one of them null and the request explicitly nulled the other. No extra check needed in the use case since step 2 already prevents an all-null body.)

7. **Mutation** — Call `review.update(rating=new_rating, comment=new_comment)`. The `update()` method sets `_rating`, `_comment`, and `_updated_at = datetime.now(UTC)`. _(This method does not yet exist on `ReviewEntity` and must be added.)_

8. **Persist** — `await self._review_repo.save(review)`. The repository calls `session.merge(model)` but does not commit.

9. **Commit** — `await self._db_session.commit()`.

10. **Return** — Build and return `UpdateReviewResult` with all fields from the updated entity.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                         |
| -------------- | ------ | --------------------------------------------- |
| `ReviewEntity` | Write  | Add `update(rating, comment)` mutation method |

### Repository Methods Required

| Interface           | Method                                               | New?          |
| ------------------- | ---------------------------------------------------- | ------------- |
| `IReviewRepository` | `save(review)`                                       | No (existing) |
| `IReviewRepository` | `find_by_id(review_id: str) -> ReviewEntity \| None` | Yes           |

### New DTOs

| DTO Class             | Type            | Fields                                                                                                                                                                 |
| --------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UpdateReviewCommand` | Command (input) | `user_id: str`, `review_id: str`, `rating: int \| None`, `comment: str \| None`, `fields_to_update: frozenset[str]`                                                    |
| `UpdateReviewResult`  | Result (output) | `id: str`, `book_id: str`, `user_id: str \| None`, `order_item_id: str`, `rating: int \| None`, `comment: str \| None`, `created_at: datetime`, `updated_at: datetime` |

### New Domain Exceptions

| Exception Class       | File                              | Inherits          |
| --------------------- | --------------------------------- | ----------------- |
| `ReviewNotFoundError` | `app/domain/exceptions/review.py` | `DomainException` |
| `ReviewNotOwnedError` | `app/domain/exceptions/review.py` | `DomainException` |

### New Error Codes

| Constant           | Value                | Description                                       |
| ------------------ | -------------------- | ------------------------------------------------- |
| `REVIEW_NOT_FOUND` | `"REVIEW_NOT_FOUND"` | No review with the given ID exists (non-deleted)  |
| `REVIEW_NOT_OWNED` | `"REVIEW_NOT_OWNED"` | Authenticated user is not the owner of the review |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/12_review/04_update_review/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` equals the review ID in the path
- [x] `res.body.data.rating` equals the value sent in the request
- [x] `res.body.data.comment` equals the value sent in the request
- [x] `res.body.data.updated_at` is later than `res.body.data.created_at`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_review_not_found.bru` — Status 404 when `review_id` does not exist → error code `REVIEW_NOT_FOUND`
- [x] `03_no_fields.bru` — Status 400 when body has neither `rating` nor `comment` → error code `VALIDATION_ERROR`
- [x] `04_invalid_rating.bru` — Status 422 when `rating` is outside 1–5 → error code `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_review.py`

**Happy Path:**

- [x] `UpdateReviewUseCase.execute(valid_command)` returns `UpdateReviewResult` with updated `rating`, `comment`, and a `updated_at` after the original

**Error Cases:**

- [x] Raises `ReviewNotFoundError` when `review_repo.find_by_id()` returns `None`
- [x] Raises `ReviewNotOwnedError` when `review.user_id != cmd.user_id`

**Edge Cases:**

- [x] Only `rating` in `fields_to_update` — `comment` retains the existing value from the stored review
- [x] Only `comment` in `fields_to_update` — `rating` retains the existing value from the stored review
- [x] `rating=None` explicitly provided — review's rating is cleared to `None`

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/review_entity.py`) — add `update(rating, comment)` method
- [x] 2. Domain exceptions (`app/domain/exceptions/review.py`) — add `ReviewNotFoundError`, `ReviewNotOwnedError`; export both from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface method (`app/domain/repositories/review_repository.py`) — add `find_by_id(review_id: str) -> ReviewEntity | None`
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — add `UpdateReviewCommand`, `UpdateReviewResult`
- [x] 5. Use case (`app/application/use_cases/review/update_review.py`) — new file `UpdateReviewUseCase`
- [x] 6. ORM model — no changes (existing `ReviewModel`)
- [x] 7. Mapper — no changes (existing `ReviewMapper`)
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/review_repository_impl.py`) — implement `find_by_id()`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — map `ReviewNotFoundError` → 404 `REVIEW_NOT_FOUND`; `ReviewNotOwnedError` → 403 `REVIEW_NOT_OWNED`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `REVIEW_NOT_FOUND`, `REVIEW_NOT_OWNED`
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — add `UpdateReviewRequest`, `UpdateReviewResponse`
- [x] 12. Route handler — add `PATCH /reviews/{review_id}` to the existing reviews router
- [x] 13. Wire in `deps.py` — no new wiring needed (review repo already registered)
- [x] 14. Alembic migration — not needed (no schema changes)
- [x] 15. Bruno test files (`bruno/12_review/04_update_review/` — `folder.bru` + 5 test files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_review.py`)
