# Author API Set — Soft Delete Author Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 6. Author             |
| Use Case     | 5. Soft Delete Author |
| File Index   | 06_05                 |
| Access Level | 🔑 Admin              |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | DELETE                            |
| URL    | `/api/app/v1/authors/{author_id}` |
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
| `author_id` | string (UUID) | ID of the author to delete |

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
    "message": "Author deleted successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                               |
| ----------- | ----------------------- | ------------------------------------------------------- |
| 401         | `INVALID_TOKEN`         | Bearer token is missing, expired, or invalid            |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have the `ADMIN` role       |
| 404         | `AUTHOR_NOT_FOUND`      | No non-deleted author exists with the given `author_id` |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure (malformed UUID path param) |

---

## Procedures

1. **Auth guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the revocation blocklist in Redis, loads the user, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure without reaching the use case.
2. **Fetch author** — Call `await self._author_repo.find_by_id(cmd.author_id)`. The repository filters `AuthorModel.deleted_at.is_(None)`, so already-deleted authors are invisible.
3. **Not-found check** — If the result is `None`, raise `AuthorNotFoundError(cmd.author_id)`. The `domain_exception_handler` maps this to HTTP 404 with error code `AUTHOR_NOT_FOUND`.
4. **Soft-delete mutation** — Call `author.soft_delete()`. This sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)` on the entity.
5. **Persist** — Call `await self._author_repo.save(author)`. The repository maps the entity (including `deleted_at`) back to `AuthorModel` and calls `session.merge(model)`. The repo does NOT commit.
6. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.
7. **Return** — Return `SoftDeleteAuthorResult(message="Author deleted successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                                                                                                          |
| -------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| `AuthorEntity` | Write  | Requires adding `_deleted_at: datetime \| None` and `soft_delete()` method — currently missing from the entity |

### Repository Methods Required

| Interface           | Method                       | New?                                                             |
| ------------------- | ---------------------------- | ---------------------------------------------------------------- |
| `IAuthorRepository` | `find_by_id(author_id: str)` | No (existing) — must be updated to filter `deleted_at.is_(None)` |
| `IAuthorRepository` | `save(author: AuthorEntity)` | No (existing) — must persist `deleted_at` via mapper             |

> **Note:** `AuthorModel` currently does not inherit `SoftDeleteMixin`, so `deleted_at` column does not exist yet. `AuthorEntity` has no `_deleted_at` field. Both must be updated as part of this implementation, and an Alembic migration is required.

### New DTOs

| DTO Class                 | Type            | Fields           |
| ------------------------- | --------------- | ---------------- |
| `SoftDeleteAuthorCommand` | Command (input) | `author_id: str` |
| `SoftDeleteAuthorResult`  | Result (output) | `message: str`   |

### New Domain Exceptions

_(None — `AuthorNotFoundError` already exists in `app/domain/exceptions/author.py`)_

### New Error Codes

_(None — `AUTHOR_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/author/soft_delete_author/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Author deleted successfully."`
- [x] `res.body.meta.requestId` is a string
- [x] Subsequent GET `/authors/{author_id}` returns 404 (author no longer visible)

**Error Cases:**

- [x] `02_forbidden_not_admin.bru` — Status 403 when authenticated as USER role → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_not_found.bru` — Status 404 when `author_id` does not exist → error code `AUTHOR_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_author.py`

**Happy Path:**

- [x] `SoftDeleteAuthorUseCase.execute(valid_command)` returns `SoftDeleteAuthorResult` with `message="Author deleted successfully."`
- [x] `author.soft_delete()` is called and `author.deleted_at` is no longer `None`
- [x] `author_repo.save()` is called once with the mutated entity
- [x] `db_session.commit()` is called once

**Error Cases:**

- [x] Raises `AuthorNotFoundError` when `author_repo.find_by_id()` returns `None`

**Edge Cases:**

- [x] Use case is idempotent at the repo layer: calling `find_by_id` on an already-deleted author returns `None` (repo filters `deleted_at.is_(None)`)

---

## Implementation Checklist

- [x] 1. Domain entity — update `AuthorEntity` in `app/domain/entities/author_entity.py`: add `_deleted_at: datetime | None`, `deleted_at` property, and `soft_delete()` method
- [x] 2. Domain exceptions — none needed (existing `AuthorNotFoundError`)
- [x] 3. Repository interface method(s) — no new abstract methods; update `find_by_id` note about `deleted_at` filter; `save()` already exists
- [x] 4. DTOs — add `SoftDeleteAuthorCommand` and `SoftDeleteAuthorResult` to `app/application/dtos/author_dto.py`
- [x] 5. Use case — create `app/application/use_cases/author/soft_delete_author.py` with `SoftDeleteAuthorUseCase`
- [x] 6. ORM model — add `SoftDeleteMixin` to `AuthorModel` in `app/infrastructure/db/models/author_model.py`
- [x] 7. Mapper — update `AuthorMapper` to map `deleted_at` in both `to_entity` and `to_model`
- [x] 8. Repository implementation — update `AuthorRepositoryImpl.find_by_id` to filter `AuthorModel.deleted_at.is_(None)`; update `save` to persist `deleted_at`
- [x] 9. Exception mapping — no changes needed (`AuthorNotFoundError` already mapped)
- [x] 10. Error codes — no changes needed (`AUTHOR_NOT_FOUND` already exists)
- [x] 11. Pydantic schemas — add `SoftDeleteAuthorResponse` to `app/presentation/schemas/author_schema.py`
- [x] 12. Route handler — add `DELETE /authors/{author_id}` to `app/presentation/api/app_api/v1/author_routes.py`
- [x] 13. Wire in `deps.py` — no changes needed (`AuthorRepo` alias already wired)
- [x] 14. Alembic migration — `make migrate msg="add deleted_at to authors"` (adds `deleted_at` nullable timestamp column to `authors` table)
- [x] 15. Bruno test files — `bruno/author/soft_delete_author/` with `folder.bru` + `01_success.bru` + `02`–`05` error cases
- [x] 16. Pytest unit tests — `backend/tests/unit/test_soft_delete_author.py`
