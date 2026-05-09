# Category API Set — Update Category Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 5. Category        |
| Use Case     | 4. Update Category |
| File Index   | 05_04              |
| Access Level | 🔑 Admin           |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | PATCH                                  |
| URL    | `/api/app/v1/categories/{category_id}` |
| Auth   | Bearer token (ADMIN role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter   | Type          | Description                      |
| ----------- | ------------- | -------------------------------- |
| category_id | string (UUID) | The ID of the category to update |

### Query Parameters

_(None)_

### Request Body

| Field         | Type   | Required | Constraints                          |
| ------------- | ------ | -------- | ------------------------------------ |
| name          | string | Yes      | 1–100 characters                     |
| url_slug      | string | Yes      | 1–100 characters                     |
| collection_id | string | Yes      | Valid UUID of an existing collection |

**Example:**

```json
{
  "name": "Science Fiction",
  "url_slug": "science-fiction",
  "collection_id": "01932abc-0000-7000-0000-000000000001"
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
    "id": "01932abc-0000-7000-0000-000000000002",
    "collection_id": "01932abc-0000-7000-0000-000000000001",
    "name": "Science Fiction",
    "url_slug": "science-fiction",
    "created_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                | Condition                                                          |
| ----------- | ------------------------- | ------------------------------------------------------------------ |
| 401         | `UNAUTHORIZED`            | No Authorization header provided                                   |
| 401         | `INVALID_TOKEN`           | Bearer token is expired or invalid                                 |
| 403         | `ADMIN_ACCESS_REQUIRED`   | Authenticated user does not have ADMIN role                        |
| 404         | `CATEGORY_NOT_FOUND`      | No live category found for `category_id`                           |
| 404         | `COLLECTION_NOT_FOUND`    | The `collection_id` in the body does not match any live collection |
| 409         | `CATEGORY_ALREADY_EXISTS` | Another category (different ID) already has the given `url_slug`   |
| 422         | `UNPROCESSABLE_ENTITY`    | Pydantic validation failure (missing fields, length violations)    |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, confirms the user is active and has `role == UserRole.ADMIN`. Returns 403 `ADMIN_ACCESS_REQUIRED` if the role check fails; 401 on token failures.

2. **Input validation** — FastAPI/Pydantic validates the request body against `UpdateCategoryRequest`. Returns 422 automatically if `name` or `url_slug` are missing or exceed their length bounds, or if `collection_id` is absent.

3. **Category existence check** — Call `category_repo.find_by_id(category_id)`. If the result is `None`, raise `CategoryNotFoundError(category_id)` → 404 `CATEGORY_NOT_FOUND`.

4. **Collection existence check** — If `cmd.collection_id` differs from `category.collection_id`, call `collection_repo.find_by_id(cmd.collection_id)`. If `None`, raise `CollectionNotFoundError(cmd.collection_id)` → 404 `COLLECTION_NOT_FOUND`. (Skip the lookup when the collection is unchanged to avoid an unnecessary query.)

5. **URL slug uniqueness check** — If `cmd.url_slug` differs from `category.url_slug`, call `category_repo.find_by_url_slug(cmd.url_slug)`. If a result is returned and its `id != category_id`, raise `CategoryAlreadyExistsError(cmd.url_slug)` → 409 `CATEGORY_ALREADY_EXISTS`.

6. **Mutation** — Call `category.update(name=cmd.name, url_slug=cmd.url_slug)`. This sets `_name`, `_url_slug`, and `_updated_at = datetime.now(UTC)` on the entity. Then set `category._collection_id = cmd.collection_id` directly (the entity has no dedicated method for reassigning the collection, so the use case sets the private field).

7. **Persist** — Call `await category_repo.save(category)`. The repository does NOT commit.

8. **Commit** — Call `await self._db_session.commit()`.

9. **Return** — Build and return `UpdateCategoryResult(id=category.id, collection_id=category.collection_id, name=category.name, url_slug=category.url_slug, created_at=category.created_at)`.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                                                 |
| ------------------ | ------ | --------------------------------------------------------------------- |
| `CategoryEntity`   | Write  | Fields mutated: `_name`, `_url_slug`, `_collection_id`, `_updated_at` |
| `CollectionEntity` | Read   | Existence check only when `collection_id` changes                     |

### Repository Methods Required

| Interface               | Method                       | New?          |
| ----------------------- | ---------------------------- | ------------- |
| `ICategoryRepository`   | `find_by_id(category_id)`    | No (existing) |
| `ICategoryRepository`   | `find_by_url_slug(url_slug)` | No (existing) |
| `ICategoryRepository`   | `save(category)`             | No (existing) |
| `ICollectionRepository` | `find_by_id(collection_id)`  | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                                                                        |
| ----------------------- | --------------- | ----------------------------------------------------------------------------- |
| `UpdateCategoryCommand` | Command (input) | `category_id: str`, `collection_id: str`, `name: str`, `url_slug: str`        |
| `UpdateCategoryResult`  | Result (output) | Inherits `BaseCategoryResult` (id, collection_id, name, url_slug, created_at) |

### New Domain Exceptions

_(None — `CategoryNotFoundError`, `CategoryAlreadyExistsError`, and `CollectionNotFoundError` already exist)_

### New Error Codes

_(None — `CATEGORY_NOT_FOUND`, `CATEGORY_ALREADY_EXISTS`, and `COLLECTION_NOT_FOUND` already defined)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/category/update_category/`

- [x] `01_success.bru` — Status 200 OK; `res.body.success` is `true`; `res.body.data.name` equals updated name; `res.body.data.url_slug` equals updated slug; `res.body.meta.requestId` is a string
- [x] `02_category_not_found.bru` — Status 404 with a non-existent `category_id` → error code `CATEGORY_NOT_FOUND`
- [x] `03_collection_not_found.bru` — Status 404 when `collection_id` does not match any live collection → error code `COLLECTION_NOT_FOUND`
- [x] `04_slug_conflict.bru` — Status 409 when `url_slug` is already in use by a different category → error code `CATEGORY_ALREADY_EXISTS`
- [x] `05_validation_error.bru` — Status 422 when required fields are missing or exceed length constraints

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_category.py`

**Happy Path:**

- [x] `UpdateCategoryUseCase.execute(valid_command)` returns `UpdateCategoryResult` with the correct `name`, `url_slug`, `collection_id`, and `id`
- [x] `db_session.commit` is called exactly once on success

**Error Cases:**

- [x] Raises `CategoryNotFoundError` when `category_id` does not exist in the repository
- [x] Raises `CollectionNotFoundError` when `collection_id` does not match any live collection
- [x] Raises `CategoryAlreadyExistsError` when the new `url_slug` belongs to a different category

**Edge Cases:**

- [x] No `CollectionNotFoundError` raised when `collection_id` is unchanged (no extra repo lookup)
- [x] No `CategoryAlreadyExistsError` raised when `url_slug` is unchanged (same slug on same category)
- [x] `commit` is NOT called when any exception is raised

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/category_entity.py`) — add `reassign_collection(collection_id)` method or update `update()` signature to include `collection_id` (existing entity, minor extension)
- [x] 2. Domain exceptions (`app/domain/exceptions/`) — no new exceptions
- [x] 3. Repository interface methods (`app/domain/repositories/`) — no new methods
- [x] 4. DTOs (`app/application/dtos/category_dto.py`) — add `UpdateCategoryCommand` and `UpdateCategoryResult`
- [x] 5. Use case (`app/application/use_cases/category/update_category.py`) — new file
- [x] 6. ORM model — no schema change
- [x] 7. Mapper — no change
- [x] 8. Repository implementation — no change
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — no new entries
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — no new entries
- [x] 11. Pydantic schemas (`app/presentation/schemas/category_schema.py`) — add `UpdateCategoryRequest` and `UpdateCategoryResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/category_routes.py`) — add `PATCH /{category_id}` handler
- [x] 13. Wire in `deps.py` — `CollectionRepo` already wired; no new entries needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/category/update_category/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_category.py`)
