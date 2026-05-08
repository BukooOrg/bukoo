# Collection API Set — Create Collection Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 8. Collection API Set |
| Use Case     | 3. Create Collection  |
| File Index   | 08_03                 |
| Access Level | 🔑 Admin              |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/collections` |
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

| Field    | Type   | Required | Constraints              |
| -------- | ------ | -------- | ------------------------ |
| name     | string | Yes      | 1–100 characters         |
| url_slug | string | Yes      | 1–100 characters, unique |

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

**Status:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "01932abc-def0-7000-a000-000000000001",
    "name": "Science & Technology",
    "urlSlug": "science-and-technology",
    "categories": [],
    "createdAt": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                  | Condition                                             |
| ----------- | --------------------------- | ----------------------------------------------------- |
| 401         | `UNAUTHORIZED`              | No Authorization header provided                      |
| 401         | `TOKEN_EXPIRED`             | Bearer token is expired                               |
| 401         | `INVALID_TOKEN`             | Bearer token is malformed or invalid                  |
| 403         | `ADMIN_ACCESS_REQUIRED`     | Authenticated user does not have the ADMIN role       |
| 409         | `COLLECTION_ALREADY_EXISTS` | A collection with the given `url_slug` already exists |
| 422         | `VALIDATION_ERROR`          | Pydantic validation failure (missing/invalid field)   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, asserts `user.role == UserRole.ADMIN`, and raises `AdminAccessRequiredError` (→ HTTP 403) if not. Route handler receives a validated `UserEntity` admin.
2. **Input validation** — FastAPI parses the request body against `CreateCollectionRequest` (Pydantic schema). Returns HTTP 422 on any validation failure.
3. **Uniqueness check** — Use case calls `await self._collection_repo.find_by_url_slug(cmd.url_slug)`. If a `CollectionEntity` is returned, raise `CollectionAlreadyExistsError(cmd.url_slug)` (→ HTTP 409, error code `COLLECTION_ALREADY_EXISTS`).
4. **Entity construction** — Construct a new `CollectionEntity` with `_id=str(uuid7())`, `_name=cmd.name`, `_url_slug=cmd.url_slug`, `_created_at=datetime.now(UTC)`, `_updated_at=datetime.now(UTC)`, `_deleted_at=None`, `_categories=[]`.
5. **Persist** — Call `await self._collection_repo.save(collection)`. The repository uses `session.merge(model)` and does not commit.
6. **Commit** — Call `await self._db_session.commit()` in the use case after the successful save.
7. **Return** — Build and return `CreateCollectionResult` with `id`, `name`, `url_slug`, `created_at`, and `categories=[]`.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                  |
| ------------------ | ------ | -------------------------------------- |
| `CollectionEntity` | Write  | New instance constructed and persisted |

### Repository Methods Required

| Interface               | Method                               | New?                |
| ----------------------- | ------------------------------------ | ------------------- |
| `ICollectionRepository` | `find_by_url_slug(url_slug: str)`    | Yes (new interface) |
| `ICollectionRepository` | `save(collection: CollectionEntity)` | Yes (new interface) |

### New DTOs

| DTO Class                 | Type            | Fields                                                                              |
| ------------------------- | --------------- | ----------------------------------------------------------------------------------- |
| `CreateCollectionCommand` | Command (input) | `name: str`, `url_slug: str`                                                        |
| `CreateCollectionResult`  | Result (output) | `id: str`, `name: str`, `url_slug: str`, `created_at: datetime`, `categories: list` |

### New Domain Exceptions

| Exception Class                | File                                  | Inherits          |
| ------------------------------ | ------------------------------------- | ----------------- |
| `CollectionAlreadyExistsError` | `app/domain/exceptions/collection.py` | `DomainException` |

### New Error Codes

| Constant                    | Value                         | Description                                 |
| --------------------------- | ----------------------------- | ------------------------------------------- |
| `COLLECTION_ALREADY_EXISTS` | `"COLLECTION_ALREADY_EXISTS"` | A collection with the given url_slug exists |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/collection/create_collection/`

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.name` equals `"Science & Technology"`
- [x] `res.body.data.urlSlug` equals `"science-and-technology"`
- [x] `res.body.data.categories` is an empty array
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when authenticated as USER role → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_conflict_slug_exists.bru` — Status 409 when `url_slug` already exists → error code `COLLECTION_ALREADY_EXISTS`
- [x] `04_validation_missing_fields.bru` — Status 422 when `name` or `url_slug` is missing

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_collection.py`

**Happy Path:**

- [x] `CreateCollectionUseCase.execute(valid_command)` returns `CreateCollectionResult` with correct `name`, `url_slug`, and empty `categories`

**Error Cases:**

- [x] Raises `CollectionAlreadyExistsError` when `find_by_url_slug` returns an existing `CollectionEntity`

**Edge Cases:**

- [x] Result `id` is a non-empty UUIDv7 string
- [x] Result `categories` is an empty list on a freshly created collection

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/collection_entity.py`) — existing, no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/collection.py`) — new file with `CollectionAlreadyExistsError`; export in `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/collection_repository.py`) — new `ICollectionRepository` with `find_by_url_slug` and `save`
- [x] 4. DTOs (`app/application/dtos/collection_dto.py`) — `CreateCollectionCommand`, `CreateCollectionResult`
- [x] 5. Use case (`app/application/use_cases/collection/create_collection.py`) — `CreateCollectionUseCase`
- [x] 6. ORM model (`app/infrastructure/db/models/collection_model.py`) — existing, no changes needed
- [x] 7. Mapper (`app/infrastructure/db/mappers/collection_mapper.py`) — existing, verify `to_entity` and `to_model` cover all fields
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/collection_repository_impl.py`) — new `CollectionRepositoryImpl` implementing `ICollectionRepository`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `CollectionAlreadyExistsError → 409, COLLECTION_ALREADY_EXISTS`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `COLLECTION_ALREADY_EXISTS`
- [x] 11. Pydantic schemas (`app/presentation/schemas/collection_schema.py`) — `CreateCollectionRequest`, `CollectionResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/collection_routes.py`) — new file with `POST /collections`; register in `app/presentation/api/app_api/v1/__init__.py`
- [x] 13. Wire in `deps.py` — add `get_collection_repository` provider and `CollectionRepo` typed alias
- [x] 14. Alembic migration — not required (`collections` table already exists)
- [x] 15. Bruno test files (`bruno/collection/create_collection/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_create_collection.py`)
