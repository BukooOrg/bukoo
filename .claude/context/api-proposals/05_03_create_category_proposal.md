# Category API Set — Create Category Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 5. Category        |
| Use Case     | 3. Create Category |
| File Index   | 05_03              |
| Access Level | 🔑 Admin           |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/categories`  |
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

| Field         | Type   | Required | Constraints                                 |
| ------------- | ------ | -------- | ------------------------------------------- |
| collection_id | string | Yes      | UUID of an existing, non-deleted collection |
| name          | string | Yes      | 1–200 characters, non-empty                 |
| url_slug      | string | Yes      | 1–200 characters, must be globally unique   |

**Example:**

```json
{
  "collection_id": "01932abc-0000-7000-8000-000000000001",
  "name": "Science Fiction",
  "url_slug": "science-fiction"
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
    "id": "01932abc-0000-7000-8000-000000000010",
    "collection_id": "01932abc-0000-7000-8000-000000000001",
    "name": "Science Fiction",
    "url_slug": "science-fiction",
    "created_at": "2026-05-08T10:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-08T10:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                              |
| ----------- | ----------------------- | ------------------------------------------------------ |
| 401         | AUTH_TOKEN_INVALID      | No or invalid Bearer token                             |
| 403         | ADMIN_ACCESS_REQUIRED   | Token belongs to a USER-role account                   |
| 404         | COLLECTION_NOT_FOUND    | No active collection found for the given collection_id |
| 409         | CATEGORY_ALREADY_EXISTS | A category with the same url_slug already exists       |
| 422         | UNPROCESSABLE_ENTITY    | Pydantic validation failure (missing/invalid fields)   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency validates the Bearer token, confirms `role == ADMIN`, and returns the authenticated `UserEntity`. Any token or role failure is handled entirely in `deps.py` before the use case runs.

2. **Input validation** — FastAPI/Pydantic validates `CreateCategoryRequest` (`collection_id`, `name`, `url_slug` all present and non-empty). Returns HTTP 422 automatically on failure.

3. **Collection existence check** — `await self._collection_repo.find_by_id(command.collection_id)`. If `None`, raise `CollectionNotFoundError(command.collection_id)`.

4. **URL slug uniqueness check** — `await self._category_repo.find_by_url_slug(command.url_slug)`. If a record is returned, raise `CategoryAlreadyExistsError(command.url_slug)`.

5. **Create entity** — Construct a new `CategoryEntity` with:
   - `_id = str(uuid7())`
   - `_collection_id = command.collection_id`
   - `_name = command.name`
   - `_url_slug = command.url_slug`
   - `_created_at = datetime.now(UTC)`
   - `_updated_at = datetime.now(UTC)`
   - `_deleted_at = None`

6. **Persist** — `await self._category_repo.save(category)`. The repository must NOT commit.

7. **Commit** — `await self._db_session.commit()`.

8. **Return** — Build and return `CreateCategoryResult` with all fields from the saved `CategoryEntity`.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                             |
| ------------------ | ------ | --------------------------------- |
| `CategoryEntity`   | Write  | New entity created                |
| `CollectionEntity` | Read   | Existence check only; no mutation |

### Repository Methods Required

| Interface               | Method                       | New?                |
| ----------------------- | ---------------------------- | ------------------- |
| `ICollectionRepository` | `find_by_id(collection_id)`  | No (existing)       |
| `ICategoryRepository`   | `find_by_url_slug(url_slug)` | Yes (new interface) |
| `ICategoryRepository`   | `save(category)`             | Yes (new interface) |

### New DTOs

| DTO Class               | Type            | Fields                                                                                |
| ----------------------- | --------------- | ------------------------------------------------------------------------------------- |
| `CreateCategoryCommand` | Command (input) | `collection_id: str`, `name: str`, `url_slug: str`                                    |
| `CreateCategoryResult`  | Result (output) | `id: str`, `collection_id: str`, `name: str`, `url_slug: str`, `created_at: datetime` |

### New Domain Exceptions

| Exception Class              | File                                | Inherits          |
| ---------------------------- | ----------------------------------- | ----------------- |
| `CategoryAlreadyExistsError` | `app/domain/exceptions/category.py` | `DomainException` |
| `CategoryNotFoundError`      | `app/domain/exceptions/category.py` | `DomainException` |

_(`CategoryNotFoundError` is added here for completeness — it will be required by use cases 5.2, 5.4, and 5.5.)_

### New Error Codes

| Constant                  | Value                       | Description                                  |
| ------------------------- | --------------------------- | -------------------------------------------- |
| `CATEGORY_ALREADY_EXISTS` | `"CATEGORY_ALREADY_EXISTS"` | A category with that url_slug already exists |
| `CATEGORY_NOT_FOUND`      | `"CATEGORY_NOT_FOUND"`      | No active category found for the given ID    |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/category/create_category/`

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.data.collection_id` equals the sent `collection_id`
- [x] `res.body.data.name` equals the sent `name`
- [x] `res.body.data.url_slug` equals the sent `url_slug`
- [x] `res.body.meta.requestId` is a string

**Error Cases (one file each):**

- [x] `02_admin_only_forbidden.bru` — Status 403 when USER-role token is provided → error code `ADMIN_ACCESS_REQUIRED`
- [x] `03_collection_not_found.bru` — Status 404 when collection_id does not exist → error code `COLLECTION_NOT_FOUND`
- [x] `04_slug_conflict.bru` — Status 409 when url_slug is already taken → error code `CATEGORY_ALREADY_EXISTS`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_category.py`

**Happy Path:**

- [x] `CreateCategoryUseCase.execute(valid_command)` returns `CreateCategoryResult` with matching `collection_id`, `name`, `url_slug`, and a non-empty `id`

**Error Cases:**

- [x] Raises `CollectionNotFoundError` when collection repo returns `None` for the given `collection_id`
- [x] Raises `CategoryAlreadyExistsError` when category repo returns an existing entity for the given `url_slug`

**Edge Cases:**

- [x] Category `save` is never called when the collection existence check fails
- [x] Category `save` is never called when the url_slug uniqueness check fails

---

## Implementation Checklist

- [x] 1. Domain entity — `CategoryEntity` already exists in `app/domain/entities/category_entity.py`
- [x] 2. Domain exceptions — create `app/domain/exceptions/category.py` with `CategoryAlreadyExistsError` and `CategoryNotFoundError`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface — create `app/domain/repositories/category_repository.py` with `ICategoryRepository` (`find_by_url_slug`, `save`)
- [x] 4. DTOs — add `CreateCategoryCommand` and `CreateCategoryResult` to `app/application/dtos/category_dto.py`
- [x] 5. Use case — `app/application/use_cases/category/create_category.py` (`CreateCategoryUseCase`)
- [x] 6. ORM model — `CategoryModel` already exists in `app/infrastructure/db/models/category_model.py`
- [x] 7. Mapper — `CategoryMapper` already exists in `app/infrastructure/db/mappers/category_mapper.py`; verify `to_entity` and `to_model` are complete before implementing the repo
- [x] 8. Repository implementation — create `app/infrastructure/db/repositories/category_repository_impl.py` (`CategoryRepositoryImpl`)
- [x] 9. Exception mapping — add `CategoryAlreadyExistsError → (409, CATEGORY_ALREADY_EXISTS)` and `CategoryNotFoundError → (404, CATEGORY_NOT_FOUND)` to `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `CATEGORY_ALREADY_EXISTS` and `CATEGORY_NOT_FOUND` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `CreateCategoryRequest` and `CreateCategoryResponse` to `app/presentation/schemas/category_schema.py`
- [x] 12. Route handler — create `app/presentation/api/app_api/v1/category_routes.py` with `POST /categories`; register in `app/presentation/api/app_api/v1/__init__.py`
- [x] 13. Wire in `deps.py` — add `get_category_repository()` provider and `CategoryRepo` typed alias
- [x] 14. Alembic migration — not required (category table already exists)
- [x] 15. Bruno test files — `bruno/category/create_category/folder.bru` + `01_success.bru` + one file per error case above
- [x] 16. Pytest unit tests — `backend/tests/unit/test_create_category.py`
