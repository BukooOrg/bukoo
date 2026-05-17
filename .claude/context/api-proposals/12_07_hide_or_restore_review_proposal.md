# Review API Set — Hide Or Restore Review Proposal

## Overview

| Field        | Value                     |
| ------------ | ------------------------- |
| API Set      | 12. Review                |
| Use Case     | 7. Hide Or Restore Review |
| File Index   | 12_07                     |
| Access Level | 🔑 Admin                  |
| Status       | Approved                  |

---

## Endpoint

| Field  | Value                                        |
| ------ | -------------------------------------------- |
| Method | PATCH                                        |
| URL    | `/api/app/v1/reviews/{review_id}/visibility` |
| Auth   | Bearer token (ADMIN role)                    |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter   | Type          | Description                  |
| ----------- | ------------- | ---------------------------- |
| `review_id` | string (UUID) | ID of the review to moderate |

### Query Parameters

_(None)_

### Request Body

| Field       | Type    | Required | Constraints                      |
| ----------- | ------- | -------- | -------------------------------- |
| `is_hidden` | boolean | Yes      | `true` = hide, `false` = restore |

**Example:**

```json
{ "is_hidden": true }
```

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "01932abc-0001-7000-0000-000000000001",
    "book_id": "01932abc-0001-7000-0000-000000000002",
    "user_id": "01932abc-0001-7000-0000-000000000003",
    "order_item_id": "01932abc-0001-7000-0000-000000000004",
    "rating": 4,
    "comment": "Great read!",
    "is_hidden": true,
    "hidden_at": "2026-05-16T10:30:00Z",
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-05-16T10:30:00Z",
    "book": {
      "id": "01932abc-0001-7000-0000-000000000002",
      "title": "The Midnight Library",
      "cover_url": "https://..."
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-16T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                                |
| ----------- | -------------------- | ------------------------------------------------------------------------ |
| 401         | AUTH_TOKEN_INVALID   | No or invalid Authorization header                                       |
| 403         | PERMISSION_DENIED    | Token belongs to a `USER`-role account                                   |
| 404         | REVIEW_NOT_FOUND     | No review with the given `review_id` exists (or it was customer-deleted) |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (e.g. `is_hidden` missing)                   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency (from `deps.py`) validates the Bearer token, checks the Redis blocklist, confirms `user.role == UserRole.ADMIN`, and raises HTTP 403 if not an admin. The use case receives no user context; auth is fully handled at the route level.

2. **Input validation** — FastAPI validates the request body against `HideOrRestoreReviewRequest` (Pydantic). HTTP 422 is returned automatically on failure.

3. **Existence check** — Call `await self._review_repo.find_by_id(cmd.review_id)`. If the result is `None`, raise `ReviewNotFoundError(cmd.review_id)`. This also returns `None` for customer-soft-deleted reviews (filtered by `deleted_at IS NULL` in the repo query), so those are treated as not found.

4. **Mutation** — If `cmd.is_hidden` is `True`, call `review.hide()` on the entity (sets `_hidden_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)`). If `cmd.is_hidden` is `False`, call `review.restore()` (sets `_hidden_at = None` and `_updated_at = datetime.now(UTC)`). Both operations are idempotent: hiding an already-hidden review or restoring an already-visible review produces no logical error (state is simply reaffirmed).

5. **Persist** — Call `await self._review_repo.save(review)`. The repository writes the updated `hidden_at` and `updated_at` values via `session.merge(model)` but does not commit.

6. **Commit** — Call `await self._db_session.commit()` in the use case after the save succeeds.

7. **Return** — Build and return `HideOrRestoreReviewResult` from the mutated entity, including `hidden_at` and `is_hidden`.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                                            |
| -------------- | ------ | -------------------------------------------------------------------------------- |
| `ReviewEntity` | Write  | Gains `_hidden_at` field, `is_hidden` property, `hide()` and `restore()` methods |

### Repository Methods Required

| Interface           | Method                  | New?          |
| ------------------- | ----------------------- | ------------- |
| `IReviewRepository` | `find_by_id(review_id)` | No (existing) |
| `IReviewRepository` | `save(review)`          | No (existing) |

> **Note:** The existing `find_by_id` filters `deleted_at IS NULL` which is correct here — admin cannot operate on customer-deleted reviews. It does not filter on `hidden_at`, so hidden reviews remain accessible to admin. The `ReviewModel` mapper and `save()` implementation must be updated to include the new `hidden_at` column.

### New DTOs

| DTO Class                    | Type            | Fields                                                                                                                                         |
| ---------------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `HideOrRestoreReviewCommand` | Command (input) | `review_id: str`, `is_hidden: bool`                                                                                                            |
| `HideOrRestoreReviewResult`  | Result (output) | `id`, `book_id`, `user_id`, `order_item_id`, `rating`, `comment`, `is_hidden: bool`, `hidden_at: datetime \| None`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — `ReviewNotFoundError` already covers the only failure case.)_

### New Error Codes

_(None — `REVIEW_NOT_FOUND` already registered in `ErrorCode` and `EXCEPTION_MAP`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/07_hide_or_restore_review/`

Each test case is a separate `.bru` file.

**`01_success_hide.bru` — Happy Path (Hide):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.is_hidden` is `true`
- [x] `res.body.data.hidden_at` is a non-null ISO string
- [x] `res.body.meta.requestId` is a string

**`02_success_restore.bru` — Happy Path (Restore):**

- [x] Status 200 OK
- [x] `res.body.data.is_hidden` is `false`
- [x] `res.body.data.hidden_at` is `null`

**Error Cases:**

- [x] `02_review_not_found.bru` — Status 404 when `review_id` does not exist → error code `REVIEW_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_hide_or_restore_review.py`

**Happy Path:**

- [x] `HideOrRestoreReviewUseCase.execute(command with is_hidden=True)` returns `HideOrRestoreReviewResult` with `is_hidden=True` and `hidden_at` set
- [x] `HideOrRestoreReviewUseCase.execute(command with is_hidden=False)` returns `HideOrRestoreReviewResult` with `is_hidden=False` and `hidden_at` is `None`

**Error Cases:**

- [x] Raises `ReviewNotFoundError` when `review_id` does not match any record

**Edge Cases:**

- [x] Hiding an already-hidden review succeeds (idempotent, `hidden_at` updated to now)
- [x] Restoring an already-visible review succeeds (idempotent, `hidden_at` remains `None`)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/review_entity.py`) — **update existing**: add `_hidden_at: datetime | None`, `is_hidden` property, `hide()` method (sets `_hidden_at` + `_updated_at`), `restore()` method (clears `_hidden_at`, updates `_updated_at`)
- [x] 2. Domain exceptions (`app/domain/exceptions/review.py`) — _no changes_
- [x] 3. Repository interface (`app/domain/repositories/review_repository.py`) — _no changes_
- [x] 4. DTOs (`app/application/dtos/review_dto.py`) — add `HideOrRestoreReviewCommand` and `HideOrRestoreReviewResult`
- [x] 5. Use case (`app/application/use_cases/review/hide_or_restore_review.py`) — new file; export from `__init__.py`
- [x] 6. ORM model (`app/infrastructure/db/models/review_model.py`) — add `hidden_at: Mapped[datetime | None]` column
- [x] 7. Mapper (`app/infrastructure/db/mappers/review_mapper.py`) — update `to_entity()` (pass `_hidden_at=model.hidden_at`) and `to_model()` / `save` path to persist `hidden_at`
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/review_repository_impl.py`) — ensure `save()` writes `model.hidden_at = review.hidden_at`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — _no changes_
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — _no changes_
- [x] 11. Pydantic schemas (`app/presentation/schemas/review_schema.py`) — add `HideOrRestoreReviewRequest` and `HideOrRestoreReviewResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/review_routes.py`) — add `PATCH /{review_id}/visibility` handler using `AdminUser`
- [x] 13. Wire in `deps.py` — `AdminUser` already exists; _no changes_
- [x] 14. Alembic migration — **required**: `make migrate msg="add hidden_at to reviews"` (adds nullable `hidden_at` column to `reviews` table)
- [x] 15. Bruno test files (`bruno/review/06_hide_or_restore_review/` — `folder.bru` + `01_success_hide.bru` + `02_success_restore.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_hide_or_restore_review.py`)
