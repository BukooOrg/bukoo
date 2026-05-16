# Author API Set — Create Author Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 6. Author        |
| Use Case     | 3. Create Author |
| File Index   | 06_03            |
| Access Level | 🔑 Admin         |
| Status       | Implemented      |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/authors`     |
| Auth   | Bearer token (ADMIN role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

### Request Body

| Field | Type   | Required | Constraints               |
| ----- | ------ | -------- | ------------------------- |
| name  | string | Yes      | 1–255 characters, trimmed |

**Example:**

```json
{
  "name": "Fyodor Dostoevsky"
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
    "id": "01932abc-0000-7000-0000-000000000001",
    "name": "Fyodor Dostoevsky",
    "createdAt": "2026-05-09T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-09T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                  |
| ----------- | ----------------------- | ---------------------------------------------------------- |
| 401         | `UNAUTHORIZED`          | No Authorization header provided                           |
| 401         | `TOKEN_EXPIRED`         | Bearer token has expired                                   |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or invalid                       |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have ADMIN role                |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure (e.g. `name` missing or blank) |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist via `RedisCacheService`, confirms the user is active, and asserts `user.role == UserRole.ADMIN`. Raises HTTP 401/403 automatically; the use case never sees an unauthenticated call.

2. **Input validation** — FastAPI validates the request body against `CreateAuthorRequest` (Pydantic). If `name` is missing, empty, or exceeds 255 characters, FastAPI returns HTTP 422 automatically before the use case runs.

3. **Entity construction** — The use case instantiates a new `AuthorEntity` with `_id=str(uuid7())`, `_name=cmd.name` (trimmed), `_created_at=datetime.now(UTC)`, `_updated_at=datetime.now(UTC)`.

4. **Persist** — Calls `await self._author_repo.save(author)`. The repository implementation calls `session.merge(AuthorMapper.to_model(author))` but does **not** commit.

5. **Commit** — Calls `await self._db_session.commit()` in the use case, completing the unit of work.

6. **Return** — Constructs and returns `CreateAuthorResult(id=author.id, name=author.name, created_at=author.created_at)`. The route handler wraps this in a Pydantic `CreateAuthorResponse`; `ResponseFormatterMiddleware` applies the `{success, data, meta}` envelope automatically.

---

## Domain Impact

### Entities Involved

| Entity         | Access | Notes                              |
| -------------- | ------ | ---------------------------------- |
| `AuthorEntity` | Write  | Entity and ORM model already exist |

### Repository Methods Required

| Interface           | Method                               | New?                |
| ------------------- | ------------------------------------ | ------------------- |
| `IAuthorRepository` | `save(author: AuthorEntity) -> None` | Yes (new interface) |

### New DTOs

| DTO Class             | Type            | Fields                                         |
| --------------------- | --------------- | ---------------------------------------------- |
| `CreateAuthorCommand` | Command (input) | `name: str`                                    |
| `CreateAuthorResult`  | Result (output) | `id: str`, `name: str`, `created_at: datetime` |

### New Domain Exceptions

_(None — author names are not unique; no conflict check required)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/Author/Create Author/`

| File                             | Scenario                  |
| -------------------------------- | ------------------------- |
| `01_success.bru`                 | Happy path                |
| `02_validation_missing_name.bru` | Body missing `name` field |
| `03_validation_blank_name.bru`   | `name` is empty string    |

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.data.name` equals the submitted name
- [x] `res.body.data.createdAt` is an ISO 8601 datetime string
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_validation_missing_name.bru` — Status 422 when `name` is absent
- [x] `03_validation_blank_name.bru` — Status 422 when `name` is blank

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_author.py`

**Happy Path:**

- [x] `CreateAuthorUseCase.execute(CreateAuthorCommand(name="Fyodor Dostoevsky"))` returns `CreateAuthorResult` with `name == "Fyodor Dostoevsky"` and a non-empty `id`

**Edge Cases:**

- [x] Name at maximum length (255 chars) is accepted and persisted correctly
- [x] Leading/trailing whitespace in `name` is preserved as-is by the use case (trimming is Pydantic's responsibility)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/author_entity.py`) — **existing**, no changes needed
- [x] 2. Domain exceptions — **none new**
- [x] 3. Repository interface (`app/domain/repositories/author_repository.py`) — **new**: `IAuthorRepository` with `save()`
- [x] 4. DTOs (`app/application/dtos/author_dto.py`) — **new**: `CreateAuthorCommand`, `CreateAuthorResult`
- [x] 5. Use case (`app/application/use_cases/author/create_author.py`) — **new**: `CreateAuthorUseCase`
- [x] 6. ORM model (`app/infrastructure/db/models/author_model.py`) — **existing**, no changes needed
- [x] 7. Mapper (`app/infrastructure/db/mappers/author_mapper.py`) — **existing**, verify `to_model` covers all fields
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/author_repository_impl.py`) — **new**: `AuthorRepositoryImpl` with `save()`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — **no new entries**
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — **no new entries**
- [x] 11. Pydantic schemas (`app/presentation/schemas/author_schema.py`) — **new**: `CreateAuthorRequest`, `CreateAuthorResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/author_routes.py`) — **new** file with `POST /authors`
- [x] 13. Wire in `deps.py` — add `get_author_repository()` provider and `AuthorRepo` alias
- [x] 14. Register router in `app/presentation/api/app_api/v1/__init__.py`
- [x] 15. Alembic migration — **not needed** (`authors` table already exists)
- [x] 16. Bruno test files (`bruno/author/create_author/` — `folder.bru` + `01_success.bru` + `02_forbidden_non_admin.bru` + `03_validation_missing_name.bru` + `04_validation_blank_name.bru`)
- [x] 17. Pytest unit tests (`backend/tests/unit/test_create_author.py`)
