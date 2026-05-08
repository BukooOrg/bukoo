# Collection API Set — Update Collection Proposal

## Overview

| Field        | Value                |
| ------------ | -------------------- |
| API Set      | 8. Collection        |
| Use Case     | 4. Update Collection |
| File Index   | 08_04                |
| Access Level | 🔑 Admin             |
| Status       | Implemented          |

---

## Endpoint

| Field  | Value                                     |
| ------ | ----------------------------------------- |
| Method | PATCH                                     |
| URL    | `/api/app/v1/collections/{collection_id}` |
| Auth   | Bearer token (ADMIN role)                 |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter     | Type          | Description                    |
| ------------- | ------------- | ------------------------------ |
| collection_id | string (UUID) | ID of the collection to update |

### Query Parameters

_(None)_

### Request Body

| Field    | Type   | Required | Constraints                  |
| -------- | ------ | -------- | ---------------------------- |
| name     | string | Yes      | min_length=1, max_length=100 |
| url_slug | string | Yes      | min_length=1, max_length=100 |

**Example:**

```json
{
  "name": "Science & Technology",
  "url_slug": "science-and-technology"
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
    "id": "01932abc-0000-7000-8000-000000000001",
    "name": "Science & Technology",
    "url_slug": "science-and-technology",
    "categories": [],
    "created_at": "2026-01-10T09:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                | Condition                                                             |
| ----------- | ------------------------- | --------------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID        | Missing, expired, or revoked bearer token                             |
| 403         | PERMISSION_DENIED         | Authenticated user does not have ADMIN role                           |
| 404         | COLLECTION_NOT_FOUND      | No live collection exists with the given `collection_id`              |
| 409         | COLLECTION_ALREADY_EXISTS | Another live collection already uses the submitted `url_slug`         |
| 422         | UNPROCESSABLE_ENTITY      | Pydantic validation failure (missing field, type error, length check) |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the blocklist via `RedisCacheService`, loads the active user, and asserts `role == UserRole.ADMIN`. Raises HTTP 401 on token failure or HTTP 403 on insufficient role. Handled entirely by `deps.py`; the use case does not repeat this check.

2. **Input validation** — FastAPI/Pydantic validates the request body against `UpdateCollectionRequest` (min/max length on `name` and `url_slug`). Returns HTTP 422 automatically on failure.

3. **Existence check** — Call `await self._collection_repo.find_by_id(cmd.collection_id)`. If the result is `None`, raise `CollectionNotFoundError(cmd.collection_id)`.

4. **Slug uniqueness check** — If `cmd.url_slug` differs from the existing `collection.url_slug`, call `await self._collection_repo.find_by_url_slug(cmd.url_slug)`. If a record is returned (and its `id` differs from `cmd.collection_id`), raise `CollectionAlreadyExistsError(cmd.url_slug)`. Skip this check if the slug is unchanged, so admins can update `name` only without a false conflict.

5. **Domain mutation** — Call `collection.update(name=cmd.name, url_slug=cmd.url_slug)`. This sets `_name`, `_url_slug`, and `_updated_at = datetime.now(UTC)` on the entity.

6. **Persist** — Call `await self._collection_repo.save(collection)`. The repository executes `session.merge(model)` and does not commit.

7. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the unit of work.

8. **Return** — Build and return `UpdateCollectionResult` from the mutated entity fields (`id`, `name`, `url_slug`, `created_at`, `categories`).

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                                  |
| ------------------ | ------ | ------------------------------------------------------ |
| `CollectionEntity` | Write  | `update()` mutates `_name`, `_url_slug`, `_updated_at` |

### Repository Methods Required

| Interface               | Method                       | New?          |
| ----------------------- | ---------------------------- | ------------- |
| `ICollectionRepository` | `find_by_id(collection_id)`  | No (existing) |
| `ICollectionRepository` | `find_by_url_slug(url_slug)` | No (existing) |
| `ICollectionRepository` | `save(collection)`           | No (existing) |

### New DTOs

| DTO Class                 | Type            | Fields                                             |
| ------------------------- | --------------- | -------------------------------------------------- |
| `UpdateCollectionCommand` | Command (input) | `collection_id: str`, `name: str`, `url_slug: str` |
| `UpdateCollectionResult`  | Result (output) | Extends `BaseCollectionResult` (no new fields)     |

### New Domain Exceptions

_(None — `CollectionNotFoundError` and `CollectionAlreadyExistsError` already exist in `app/domain/exceptions/collection.py`)_

### New Error Codes

_(None — error codes for `COLLECTION_NOT_FOUND` and `COLLECTION_ALREADY_EXISTS` must already exist if 8.3 was implemented; confirm in `app/application/errors/error_codes.py` and add if missing)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/collection/update_collection/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.name` equals the submitted name
- [ ] `res.body.data.url_slug` equals the submitted url_slug
- [ ] `res.body.data.id` matches the path `collection_id`
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_admin_forbidden.bru` — Status 403 when authenticated as a non-admin user
- [ ] `03_not_found.bru` — Status 404 when `collection_id` does not exist → error code `COLLECTION_NOT_FOUND`
- [ ] `04_slug_conflict.bru` — Status 409 when submitted `url_slug` is already used by another collection → error code `COLLECTION_ALREADY_EXISTS`
- [ ] `05_validation_error.bru` — Status 422 when `name` is missing from the request body

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_collection.py`

**Happy Path:**

- [x] `UpdateCollectionUseCase.execute(valid_command)` returns `UpdateCollectionResult` with updated `name` and `url_slug`
- [x] `UpdateCollectionUseCase.execute(command_same_slug)` succeeds without raising when `url_slug` is unchanged

**Error Cases:**

- [x] Raises `CollectionNotFoundError` when no collection exists with the given `collection_id`
- [x] Raises `CollectionAlreadyExistsError` when the new `url_slug` belongs to a different existing collection

**Edge Cases:**

- [x] Updating only `name` while keeping the same `url_slug` does not trigger the uniqueness check

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/collection_entity.py`) — existing; `update()` method already present
- [x] 2. Domain exceptions (`app/domain/exceptions/collection.py`) — existing; `CollectionNotFoundError`, `CollectionAlreadyExistsError` already present
- [x] 3. Repository interface methods (`app/domain/repositories/collection_repository.py`) — all required methods exist
- [x] 4. DTOs (`app/application/dtos/collection_dto.py`) — add `UpdateCollectionCommand` and `UpdateCollectionResult`
- [x] 5. Use case (`app/application/use_cases/collection/update_collection.py`) — new file
- [x] 6. ORM model — no change (no schema change)
- [x] 7. Mapper — no change
- [x] 8. Repository implementation — no change
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — verify `CollectionNotFoundError` and `CollectionAlreadyExistsError` are already mapped; add if missing
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — verify `COLLECTION_NOT_FOUND` and `COLLECTION_ALREADY_EXISTS` exist; add if missing
- [x] 11. Pydantic schemas (`app/presentation/schemas/collection_schema.py`) — add `UpdateCollectionRequest`; reuse `CollectionResponse` for the response
- [x] 12. Route handler (`app/presentation/api/app_api/v1/collection_routes.py`) — add PATCH `/{collection_id}` handler
- [x] 13. Wire in `deps.py` — `CollectionRepo` alias already present; no new wiring needed
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/collection/update_collection/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_collection.py`)
