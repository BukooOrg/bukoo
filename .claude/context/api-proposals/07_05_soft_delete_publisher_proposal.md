# Publisher API Set — Soft Delete Publisher Proposal

## Overview

| Field        | Value                    |
| ------------ | ------------------------ |
| API Set      | 7. Publisher             |
| Use Case     | 5. Soft Delete Publisher |
| File Index   | 07_05                    |
| Access Level | 🔑 Admin                 |
| Status       | Implemented              |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | DELETE                                  |
| URL    | `/api/app/v1/publishers/{publisher_id}` |
| Auth   | Bearer token (ADMIN role)               |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter      | Type          | Description                   |
| -------------- | ------------- | ----------------------------- |
| `publisher_id` | string (UUID) | ID of the publisher to delete |

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
    "message": "Publisher deleted successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                     |
| ----------- | ----------------------- | ------------------------------------------------------------- |
| 401         | `INVALID_TOKEN`         | Bearer token is missing, expired, or invalid                  |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have the `ADMIN` role             |
| 404         | `PUBLISHER_NOT_FOUND`   | No non-deleted publisher exists with the given `publisher_id` |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure (malformed UUID path param)       |

---

## Procedures

1. **Auth guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the revocation blocklist in Redis, loads the user, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure without reaching the use case.
2. **Fetch publisher** — Call `await self._publisher_repo.find_by_id(cmd.publisher_id)`. The repository filters `PublisherModel.deleted_at.is_(None)`, so already-deleted publishers are invisible.
3. **Not-found check** — If the result is `None`, raise `PublisherNotFoundError(cmd.publisher_id)`. The `domain_exception_handler` maps this to HTTP 404 with error code `PUBLISHER_NOT_FOUND`.
4. **Soft-delete mutation** — Call `publisher.soft_delete()`. This sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)` on the entity.
5. **Persist** — Call `await self._publisher_repo.save(publisher)`. The repository maps the entity (including `deleted_at`) back to `PublisherModel` and calls `session.merge(model)`. The repo does NOT commit.
6. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.
7. **Return** — Return `SoftDeletePublisherResult(message="Publisher deleted successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                                                                                          |
| ----------------- | ------ | -------------------------------------------------------------------------------------------------------------- |
| `PublisherEntity` | Write  | Requires adding `_deleted_at: datetime \| None` and `soft_delete()` method — currently missing from the entity |

### Repository Methods Required

| Interface              | Method                             | New?                                                               |
| ---------------------- | ---------------------------------- | ------------------------------------------------------------------ |
| `IPublisherRepository` | `find_by_id(publisher_id: str)`    | No (existing) — must be updated to filter `deleted_at.is_(None)`   |
| `IPublisherRepository` | `save(publisher: PublisherEntity)` | No (existing, added in 7.4) — must persist `deleted_at` via mapper |

> **Note:** `PublisherModel` currently inherits only `DefaultFieldMixin` and has no `SoftDeleteMixin`, so the `deleted_at` column does not yet exist. `PublisherEntity` has no `_deleted_at` field. Both must be updated as part of this implementation, and an Alembic migration is required.

### New DTOs

| DTO Class                    | Type            | Fields              |
| ---------------------------- | --------------- | ------------------- |
| `SoftDeletePublisherCommand` | Command (input) | `publisher_id: str` |
| `SoftDeletePublisherResult`  | Result (output) | `message: str`      |

_(Added to existing `app/application/dtos/publisher_dto.py`)_

### New Domain Exceptions

_(None — `PublisherNotFoundError` already exists in `app/domain/exceptions/publisher.py`)_

### New Error Codes

_(None — `PUBLISHER_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/publisher/soft_delete_publisher/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Publisher deleted successfully."`
- [x] `res.body.meta.requestId` is a string
- [x] Subsequent GET `/publishers/{publisher_id}` returns 404 (publisher no longer visible)

**Error Cases:**

- [x] `02_forbidden_not_admin.bru` — Status 403 when authenticated as USER role → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_not_found.bru` — Status 404 when `publisher_id` does not exist → error code `PUBLISHER_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_publisher.py`

**Happy Path:**

- [x] `SoftDeletePublisherUseCase.execute(valid_command)` returns `SoftDeletePublisherResult` with `message="Publisher deleted successfully."`
- [x] `publisher.soft_delete()` is called and `publisher.deleted_at` is no longer `None`
- [x] `publisher_repo.save()` is called once with the mutated entity
- [x] `db_session.commit()` is called once

**Error Cases:**

- [x] Raises `PublisherNotFoundError` when `publisher_repo.find_by_id()` returns `None`

**Edge Cases:**

- [x] Use case is idempotent at the repo layer: calling `find_by_id` on an already-deleted publisher returns `None` (repo filters `deleted_at.is_(None)`)

---

## Implementation Checklist

- [x] 1. Domain entity — update `PublisherEntity` in `app/domain/entities/publisher_entity.py`: add `_deleted_at: datetime | None`, `deleted_at` property, and `soft_delete()` method
- [x] 2. Domain exceptions — none needed (existing `PublisherNotFoundError`)
- [x] 3. Repository interface — no new abstract methods; update `find_by_id` to filter `deleted_at.is_(None)`; `save()` already exists (added in 7.4)
- [x] 4. DTOs — add `SoftDeletePublisherCommand` and `SoftDeletePublisherResult` to `app/application/dtos/publisher_dto.py`
- [x] 5. Use case — create `app/application/use_cases/publisher/soft_delete_publisher.py` with `SoftDeletePublisherUseCase`
- [x] 6. ORM model — add `SoftDeleteMixin` to `PublisherModel` in `app/infrastructure/db/models/publisher_model.py`
- [x] 7. Mapper — update `PublisherMapper` to map `deleted_at` in both `to_entity` and `to_model`
- [x] 8. Repository implementation — update `PublisherRepositoryImpl.find_by_id` to filter `PublisherModel.deleted_at.is_(None)`; update `save` to persist `deleted_at`
- [x] 9. Exception mapping — no changes needed (`PublisherNotFoundError` already mapped)
- [x] 10. Error codes — no changes needed (`PUBLISHER_NOT_FOUND` already exists)
- [x] 11. Pydantic schemas — add `SoftDeletePublisherResponse` to `app/presentation/schemas/publisher_schema.py`
- [x] 12. Route handler — add `DELETE /publishers/{publisher_id}` to `app/presentation/api/app_api/v1/publisher_routes.py`
- [x] 13. Wire in `deps.py` — no changes needed (`PublisherRepo` alias already wired)
- [x] 14. Alembic migration — `make migrate msg="add deleted_at to publishers"` (adds nullable `deleted_at` timestamp column to `publishers` table)
- [x] 15. Bruno test files — `bruno/publisher/soft_delete_publisher/` with `folder.bru` + `01_success.bru` + `02`–`03` error cases
- [x] 16. Pytest unit tests — `backend/tests/unit/test_soft_delete_publisher.py`
