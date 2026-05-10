# Author API Set — Update Author Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 6. Author        |
| Use Case     | 4. Update Author |
| File Index   | 06_04            |
| Access Level | 🔑 Admin         |
| Status       | Approved         |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | PATCH                             |
| URL    | `/api/app/v1/authors/{author_id}` |
| Auth   | Bearer token (ADMIN role)         |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                      |
| --------- | ------------- | -------------------------------- |
| author_id | string (UUID) | The UUID of the author to update |

### Query Parameters

_(None)_

### Request Body

| Field | Type   | Required | Constraints                                                                                  |
| ----- | ------ | -------- | -------------------------------------------------------------------------------------------- |
| name  | string | Yes      | 2–255 characters, stripped of leading/trailing whitespace, must not be blank after stripping |

**Example:**

```json
{
  "name": "Ernest Hemingway"
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
    "id": "01932abc-1111-7000-a000-000000000001",
    "name": "Ernest Hemingway",
    "updated_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                  |
| ----------- | ----------------------- | ---------------------------------------------------------- |
| 401         | `UNAUTHORIZED`          | No Authorization header provided                           |
| 401         | `TOKEN_EXPIRED`         | Bearer token has expired                                   |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or signature is invalid          |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have the ADMIN role            |
| 404         | `AUTHOR_NOT_FOUND`      | No author with the given `author_id` exists                |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure (e.g. name too short or blank) |

---

## Procedures

1. **Auth guard** — The `AdminUser` dependency in `deps.py` validates the Bearer JWT, checks the Redis blocklist, confirms the user exists and has `role == UserRole.ADMIN`. Returns HTTP 401 if the token is missing/expired/invalid, HTTP 403 if the role is not ADMIN. The use case is never reached in these cases.

2. **Input validation** — FastAPI and Pydantic validate the request body against `UpdateAuthorRequest`. The `name` field is stripped of surrounding whitespace; if the stripped value is empty, a `ValueError` is raised and FastAPI returns HTTP 422. The name must be 2–255 characters after stripping.

3. **Existence check** — The use case calls `await self._author_repo.find_by_id(cmd.author_id)`. If the result is `None`, raise `AuthorNotFoundError(cmd.author_id)`. The exception handler maps this to HTTP 404 with error code `AUTHOR_NOT_FOUND`.

4. **Mutation** — Call `author.rename(cmd.name)`. The `rename()` method on `AuthorEntity` sets `_name = name` and `_updated_at = datetime.now(UTC)` internally.

5. **Persist** — Call `await self._author_repo.save(author)`. The repository implementation calls `session.merge(model)` and does not commit.

6. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.

7. **Return** — Build and return `UpdateAuthorResult(id=author.id, name=author.name, updated_at=author.updated_at)`.

---

## Domain Impact

### Entities Involved

| Entity         | Access       | Notes                                                        |
| -------------- | ------------ | ------------------------------------------------------------ |
| `AuthorEntity` | Read / Write | `rename()` method already exists; no entity changes required |

### Repository Methods Required

| Interface           | Method                  | New?          |
| ------------------- | ----------------------- | ------------- |
| `IAuthorRepository` | `find_by_id(author_id)` | No (existing) |
| `IAuthorRepository` | `save(author)`          | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                         |
| --------------------- | --------------- | ---------------------------------------------- |
| `UpdateAuthorCommand` | Command (input) | `author_id: str`, `name: str`                  |
| `UpdateAuthorResult`  | Result (output) | `id: str`, `name: str`, `updated_at: datetime` |

### New Domain Exceptions

_(None — `AuthorNotFoundError` already exists in `app/domain/exceptions/author.py`)_

### New Error Codes

_(None — `AUTHOR_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/author/update_author/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.name` equals the updated name sent in the request
- [x] `res.body.data.id` matches the path `author_id`
- [x] `res.body.data.updated_at` is a string (ISO timestamp)
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when authenticated as USER role → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_author_not_found.bru` — Status 404 when `author_id` does not exist → error code `AUTHOR_NOT_FOUND`
- [x] `04_validation_blank_name.bru` — Status 422 when `name` is blank/whitespace only

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_author.py`

**Happy Path:**

- [x] `UpdateAuthorUseCase.execute(valid_command)` returns `UpdateAuthorResult` with the updated name and a new `updated_at` timestamp

**Error Cases:**

- [x] Raises `AuthorNotFoundError` when `find_by_id` returns `None`

**Edge Cases:**

- [x] Name with leading/trailing spaces is stripped before being saved (validated at Pydantic layer)
- [x] `author.updated_at` in the result is strictly greater than the `created_at` stored on the entity

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/author_entity.py`) — existing, no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/author.py`) — existing `AuthorNotFoundError`, no changes needed
- [x] 3. Repository interface methods (`app/domain/repositories/author_repository.py`) — existing `find_by_id` + `save`, no changes needed
- [x] 4. DTOs (`app/application/dtos/author_dto.py`) — add `UpdateAuthorCommand` and `UpdateAuthorResult`
- [x] 5. Use case (`app/application/use_cases/author/update_author.py`) — new `UpdateAuthorUseCase`
- [x] 6. ORM model — no changes (no schema change)
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation — no changes
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — `AuthorNotFoundError` already mapped, no changes needed
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — `AUTHOR_NOT_FOUND` already exists, no changes needed
- [x] 11. Pydantic schemas (`app/presentation/schemas/author_schema.py`) — add `UpdateAuthorRequest` and `UpdateAuthorResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/author_routes.py`) — add `update_author` handler
- [x] 13. Wire in `deps.py` — `AuthorRepo` already wired, no changes needed
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/author/update_author/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_author.py`)
