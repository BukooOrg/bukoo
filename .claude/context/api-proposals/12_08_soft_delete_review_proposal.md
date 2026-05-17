# Review API Set — Soft Delete Review Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 12. Review API Set    |
| Use Case     | 8. Soft Delete Review |
| File Index   | 12_08                 |
| Access Level | 🔑 Admin              |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | DELETE                            |
| URL    | `/api/app/v1/reviews/{review_id}` |
| Auth   | Bearer token (ADMIN role)         |

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

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 204 No Content

_(Empty body — no envelope wrapper for 204 responses)_

### Error Responses

| HTTP Status | Error Code              | Condition                                             |
| ----------- | ----------------------- | ----------------------------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`    | No or invalid Bearer token                            |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have ADMIN role           |
| 404         | `REVIEW_NOT_FOUND`      | No live (non-deleted) review exists with the given ID |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure on path parameter         |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and asserts `user.role == UserRole.ADMIN`. Returns 403 with `ADMIN_ACCESS_REQUIRED` if the role check fails; returns 401 on token errors.

2. **Existence check** — Call `await review_repo.find_by_id(review_id)`. The repository filters `ReviewModel.deleted_at.is_(None)`, so already-deleted reviews are invisible. If the result is `None`, raise `ReviewNotFoundError(review_id)` → 404 `REVIEW_NOT_FOUND`.

3. **Soft delete** — Call `review.soft_delete()` on the entity. This sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)`.

4. **Persist** — Call `await review_repo.save(review)`. The repository does NOT commit.

5. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.

6. **Return** — Return `None`. The route handler responds with HTTP 204 No Content.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                |
| -------------- | ------ | ---------------------------------------------------- |
| `ReviewEntity` | Write  | `soft_delete()` sets `_deleted_at` and `_updated_at` |

### Repository Methods Required

| Interface           | Method                  | New?          |
| ------------------- | ----------------------- | ------------- |
| `IReviewRepository` | `find_by_id(review_id)` | No (existing) |
| `IReviewRepository` | `save(review)`          | No (existing) |

### New DTOs

| DTO Class                 | Type            | Fields           |
| ------------------------- | --------------- | ---------------- |
| `SoftDeleteReviewCommand` | Command (input) | `review_id: str` |

### New Domain Exceptions

_(None — `ReviewNotFoundError` already exists in `app/domain/exceptions/review.py`)_

### New Error Codes

_(None — `REVIEW_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/review/08_soft_delete_review/`

| File                      | seq | Scenario                       |
| ------------------------- | --- | ------------------------------ |
| `01_success.bru`          | 1   | Happy path                     |
| `02_review_not_found.bru` | 2   | Non-existent `review_id` → 404 |

**`01_success.bru` — Happy Path:**

- [x] Status 204 No Content
- [x] Response body is empty

**Error Cases:**

- [x] `02_review_not_found.bru` — Status 404 when `review_id` does not match any live review → error code `REVIEW_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_review.py`

**Happy Path:**

- [x] `SoftDeleteReviewUseCase.execute(valid_command)` returns `None` and `review.soft_delete()` is called (verify `review.deleted_at` is set)

**Error Cases:**

- [x] Raises `ReviewNotFoundError` when no review with the given ID exists in the repository

---

## Implementation Checklist

- [x] 1. Domain entity — `ReviewEntity` exists; `soft_delete()` method already present
- [x] 2. Domain exceptions — `ReviewNotFoundError` exists; nothing to add
- [x] 3. Repository interface methods — `find_by_id` and `save` exist; nothing to add
- [x] 4. DTOs — add `SoftDeleteReviewCommand` to `app/application/dtos/review_dto.py`
- [x] 5. Use case — `app/application/use_cases/review/soft_delete_review.py` (`SoftDeleteReviewUseCase`)
- [x] 6. ORM model — `ReviewModel` exists; no schema change
- [x] 7. Mapper — `ReviewMapper` exists; no change
- [x] 8. Repository implementation — `ReviewRepositoryImpl` exists; no new methods
- [x] 9. Exception mapping — `ReviewNotFoundError` already mapped in `exception_mapper.py`; nothing to add
- [x] 10. Error codes — `REVIEW_NOT_FOUND` already exists; nothing to add
- [x] 11. Pydantic schemas — no request/response schema needed (no body, 204 response)
- [x] 12. Route handler — add `DELETE /{review_id}` handler to `app/presentation/api/app_api/v1/review_routes.py`
- [x] 13. Wire in `deps.py` — `ReviewRepo` and `AdminUser` aliases already exist
- [x] 14. Alembic migration — no schema change; skip
- [x] 15. Bruno test files — `bruno/review/08_soft_delete_review/` (`folder.bru` + `01_success.bru` + `02_review_not_found.bru`)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_soft_delete_review.py`
