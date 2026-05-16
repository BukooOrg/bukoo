# Collection API Set — Soft Delete Collection Proposal

## Overview

| Field        | Value                     |
| ------------ | ------------------------- |
| API Set      | 8. Collection             |
| Use Case     | 5. Soft Delete Collection |
| File Index   | 08_05                     |
| Access Level | 🔑 Admin                  |
| Status       | Implemented               |

---

## Endpoint

| Field  | Value                                     |
| ------ | ----------------------------------------- |
| Method | DELETE                                    |
| URL    | `/api/app/v1/collections/{collection_id}` |
| Auth   | Bearer token (ADMIN role)                 |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter     | Type          | Description                         |
| ------------- | ------------- | ----------------------------------- |
| collection_id | string (UUID) | ID of the collection to soft-delete |

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
    "message": "Collection deleted successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                     |
| ----------- | ----------------------- | --------------------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`    | Bearer token missing, expired, or invalid     |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have ADMIN role   |
| 404         | `COLLECTION_NOT_FOUND`  | No active collection with the given ID exists |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure                   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token and enforces `UserRole.ADMIN`. Returns HTTP 401/403 before the handler body executes if the token is invalid or the role is wrong.
2. **Fetch collection** — Call `await self._collection_repo.find_by_id(cmd.collection_id)`. If the result is `None`, raise `CollectionNotFoundError(cmd.collection_id)`.
3. **Soft-delete entity** — Call `collection.soft_delete()`. This sets `_deleted_at = datetime.now(UTC)` and updates `_updated_at` on the `CollectionEntity`. The cascade soft-delete of all child categories is handled in the DB layer (the repository implementation bulk-updates `categories.deleted_at` for the collection's ID).
4. **Persist** — Call `await self._collection_repo.save(collection)`. The repository implementation also bulk-sets `deleted_at` on all `CategoryModel` rows where `collection_id` matches and `deleted_at IS NULL`. The repository does NOT commit.
5. **Commit** — Call `await self._db_session.commit()` in the use case after all mutations.
6. **Return** — Return `SoftDeleteCollectionResult(message="Collection deleted successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                              |
| ------------------ | ------ | -------------------------------------------------- |
| `CollectionEntity` | Write  | `soft_delete()` sets `_deleted_at`                 |
| `CategoryEntity`   | Write  | Cascaded in DB — bulk `deleted_at` update via repo |

### Repository Methods Required

| Interface               | Method                                       | New?          |
| ----------------------- | -------------------------------------------- | ------------- |
| `ICollectionRepository` | `find_by_id(collection_id)`                  | No (existing) |
| `ICollectionRepository` | `save(collection)`                           | No (existing) |
| `ICollectionRepository` | `soft_delete_with_categories(collection_id)` | Yes           |

> **Note on cascade:** The cleanest approach is a dedicated `soft_delete_with_categories` repository method that issues a bulk `UPDATE categories SET deleted_at = now() WHERE collection_id = :id AND deleted_at IS NULL` within the same session before merging the collection model. This keeps the cascade in the infrastructure layer without loading all category entities into memory.

### New DTOs

| DTO Class                     | Type            | Fields               |
| ----------------------------- | --------------- | -------------------- |
| `SoftDeleteCollectionCommand` | Command (input) | `collection_id: str` |
| `SoftDeleteCollectionResult`  | Result (output) | `message: str`       |

### New Domain Exceptions

_(None — `CollectionNotFoundError` already exists)_

### New Error Codes

_(None — `COLLECTION_NOT_FOUND` already exists)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/collection/soft_delete_collection/`

| File                         | Scenario                                                                     |
| ---------------------------- | ---------------------------------------------------------------------------- |
| `01_success.bru`             | Status 200; `res.body.success` is `true`; `res.body.data.message` is present |
| `02_forbidden_non_admin.bru` | Status 403 when authenticated user has `USER` role → `ADMIN_ACCESS_REQUIRED` |
| `03_not_found.bru`           | Status 404 with non-existent `collection_id` → `COLLECTION_NOT_FOUND`        |

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_collection.py`

**Happy Path:**

**Error Cases:**

- [x] # Raises `CollectionNotFoundError` when `find_by_id` returns `None`
- [x] `SoftDeleteCollectionUseCase.execute(valid_command)` returns `SoftDeleteCollectionResult` with `message = "Collection deleted successfully."`
- [x] `collection.soft_delete()` is called (entity's `deleted_at` is set)
- [x] `collection_repo.save()` is called once
- [x] `db_session.commit()` is called once

---

## Implementation Checklist

- [x] 1. Domain entity — existing `CollectionEntity` already has `soft_delete()` method ✓
- [x] 2. Domain exceptions — existing `CollectionNotFoundError` ✓
- [x] 3. Repository interface — add `soft_delete_with_categories(collection_id: str)` to `ICollectionRepository`
- [x] 4. DTOs — add `SoftDeleteCollectionCommand` and `SoftDeleteCollectionResult` to `app/application/dtos/collection_dto.py`
- [x] 5. Use case — `app/application/use_cases/collection/soft_delete_collection.py`
- [x] 6. ORM model — no schema change needed
- [x] 7. Mapper — no change needed
- [x] 8. Repository implementation — implement `soft_delete_with_categories` in `CollectionRepositoryImpl` (bulk UPDATE on categories + merge collection model)
- [x] 9. Exception mapping — existing `CollectionNotFoundError` mapping ✓
- [x] 10. Error codes — existing `COLLECTION_NOT_FOUND` ✓
- [x] 11. Pydantic schemas — add `SoftDeleteCollectionResponse` to `app/presentation/schemas/collection_schema.py`
- [x] 12. Route handler — add `DELETE /{collection_id}` to `app/presentation/api/app_api/v1/collection_routes.py`
- [x] 13. Wire in `deps.py` — no new dependency needed (uses existing `CollectionRepo`)
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/collection/soft_delete_collection/` with `folder.bru` + 3 test files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_soft_delete_collection.py`
