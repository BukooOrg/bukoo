# Category API Set — Soft Delete Category Proposal

## Overview

| Field        | Value                   |
| ------------ | ----------------------- |
| API Set      | 5. Category             |
| Use Case     | 5. Soft Delete Category |
| File Index   | 05_05                   |
| Access Level | 🔑 Admin                |
| Status       | Implemented             |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | DELETE                                 |
| URL    | `/api/app/v1/categories/{category_id}` |
| Auth   | Bearer token (ADMIN role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter   | Type          | Description                       |
| ----------- | ------------- | --------------------------------- |
| category_id | string (UUID) | ID of the category to soft-delete |

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
    "message": "Category deleted successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                   |
| ----------- | ----------------------- | ------------------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`    | Bearer token missing, expired, or invalid   |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have ADMIN role |
| 404         | `CATEGORY_NOT_FOUND`    | No live category exists with the given ID   |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure on path param   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token and asserts `role == UserRole.ADMIN`; raises HTTP 403 with `ADMIN_ACCESS_REQUIRED` if the role check fails. Not handled by the use case.
2. **Existence check** — call `await self._category_repo.find_by_id(cmd.category_id)`. Because `find_by_id` filters `deleted_at IS NULL`, a missing or already-deleted category both return `None`. Raise `CategoryNotFoundError(cmd.category_id)` if the result is `None`.
3. **Soft-delete entity** — call `category.soft_delete()`, which sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)` on the entity.
4. **Nullify associated books** — call `await self._category_repo.nullify_books_category(cmd.category_id)` to execute a bulk `UPDATE books SET category_id = NULL WHERE category_id = :id AND deleted_at IS NULL`. This dissociates all live books from the deleted category without touching the books' `deleted_at`.
5. **Persist** — call `await self._category_repo.save(category)` to flush the soft-deleted entity. The repository must not commit.
6. **Commit** — call `await self._db_session.commit()` to atomically apply both the category soft-delete and the book nullification.
7. **Return** — return `SoftDeleteCategoryResult(message="Category deleted successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity           | Access | Notes                                           |
| ---------------- | ------ | ----------------------------------------------- |
| `CategoryEntity` | Write  | `soft_delete()` method already exists           |
| `BookEntity`     | Write  | `category_id` set to `NULL` via bulk repo query |

### Repository Methods Required

| Interface             | Method                                     | New?          |
| --------------------- | ------------------------------------------ | ------------- |
| `ICategoryRepository` | `find_by_id(category_id)`                  | No (existing) |
| `ICategoryRepository` | `save(category)`                           | No (existing) |
| `ICategoryRepository` | `nullify_books_category(category_id: str)` | Yes           |

### New DTOs

| DTO Class                   | Type            | Fields             |
| --------------------------- | --------------- | ------------------ |
| `SoftDeleteCategoryCommand` | Command (input) | `category_id: str` |
| `SoftDeleteCategoryResult`  | Result (output) | `message: str`     |

### New Domain Exceptions

_(None — `CategoryNotFoundError` already exists in `app/domain/exceptions/category.py`)_

### New Error Codes

_(None — `CATEGORY_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/category/soft_delete_category/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Category deleted successfully."`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when authenticated as a non-admin user → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_not_found.bru` — Status 404 when `category_id` does not match any live category → error code `CATEGORY_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_category.py`

**Happy Path:**

- [x] `SoftDeleteCategoryUseCase.execute(valid_command)` returns `SoftDeleteCategoryResult` with `message == "Category deleted successfully."`
- [x] `category.deleted_at` is set after execution (not `None`)
- [x] `repo.save()` is called with the soft-deleted entity
- [x] `repo.nullify_books_category()` is called with the correct `category_id`
- [x] `db_session.commit()` is called exactly once

**Error Cases:**

- [x] Raises `CategoryNotFoundError` when no live category exists for the given ID

---

## Implementation Checklist

- [x] 1. Domain entity — existing (`CategoryEntity.soft_delete()` already implemented)
- [x] 2. Domain exceptions — existing (`CategoryNotFoundError` already in `app/domain/exceptions/category.py`)
- [x] 3. Repository interface method — add `nullify_books_category(category_id: str) -> None` to `ICategoryRepository` (`app/domain/repositories/category_repository.py`)
- [x] 4. DTOs — add `SoftDeleteCategoryCommand` and `SoftDeleteCategoryResult` to `app/application/dtos/category_dto.py`
- [x] 5. Use case — create `app/application/use_cases/category/soft_delete_category.py` with `SoftDeleteCategoryUseCase`
- [x] 6. ORM model — no changes (no new table)
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation — add `nullify_books_category` to `CategoryRepositoryImpl` (`app/infrastructure/db/repositories/category_repository_impl.py`); bulk-update `books` table setting `category_id = NULL` where `category_id = :id AND deleted_at IS NULL`
- [x] 9. Exception mapping — no changes (`CategoryNotFoundError` already in `EXCEPTION_MAP`)
- [x] 10. Error codes — no changes (`CATEGORY_NOT_FOUND` already exists)
- [x] 11. Pydantic schemas — add `SoftDeleteCategoryResponse` (with `message: str`) to `app/presentation/schemas/category_schema.py`
- [x] 12. Route handler — add `DELETE /{category_id}` endpoint to `app/presentation/api/app_api/v1/category_routes.py`
- [x] 13. Wire in `deps.py` — no changes (`CategoryRepo` typed alias already exists)
- [x] 14. Alembic migration — not required (no schema changes)
- [ ] 15. Bruno test files — create `bruno/category/soft_delete_category/` with `folder.bru` + `01_success.bru` + `02_forbidden_non_admin.bru` + `03_unauthorized.bru` + `04_not_found.bru`
- [ ] 16. Pytest unit tests — create `backend/tests/unit/test_soft_delete_category.py`
