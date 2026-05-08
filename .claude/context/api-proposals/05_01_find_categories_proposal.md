# Category API Set — Find Categories Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 5. Category                     |
| Use Case     | 5.1. Find Categories            |
| File Index   | 05\_01                          |
| Access Level | 🌐 Public                       |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                          |
| ------ | ------------------------------ |
| Method | GET                            |
| URL    | `/api/app/v1/categories`       |
| Auth   | None                           |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

_(None)_

### Query Parameters

| Parameter     | Type          | Required | Default | Description                                              |
| ------------- | ------------- | -------- | ------- | -------------------------------------------------------- |
| collection_id | string (UUID) | No       | —       | Filter categories to those belonging to this collection  |

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": [
    {
      "id": "01932abc-...",
      "collection_id": "01932abc-...",
      "name": "Literary Fiction",
      "url_slug": "literary-fiction",
      "created_at": "2026-01-15T10:30:00Z"
    }
  ],
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                     |
| ----------- | -------------------- | --------------------------------------------- |
| 422         | UNPROCESSABLE_ENTITY | `collection_id` is present but not a valid UUID |

---

## Procedures

1. **No auth guard** — this is a public endpoint. No `CurrentUser` dependency is needed.
2. **Input validation** — FastAPI validates the optional `collection_id` query parameter as a UUID string via the Pydantic request schema. If present and malformed, FastAPI returns HTTP 422 automatically.
3. **Fetch categories** — Call `ICategoryRepository.find_all(collection_id=collection_id)`, passing the optional filter. The repository builds a `SELECT` from `CategoryModel` where `deleted_at IS NULL`; if `collection_id` is provided it adds `.where(CategoryModel.collection_id == collection_id)`.
4. **Return result** — Map each `CategoryEntity` to a `FindCategoryItemResult` and wrap in `FindCategoriesResult(categories=[...])`. Return it to the route handler, which serialises through `CategoryListResponse`.

---

## Domain Impact

### Entities Involved

| Entity           | Access | Notes                     |
| ---------------- | ------ | ------------------------- |
| `CategoryEntity` | Read   | Filtered by soft-delete   |

### Repository Methods Required

| Interface              | Method                                                         | New? |
| ---------------------- | -------------------------------------------------------------- | ---- |
| `ICategoryRepository`  | `find_all(collection_id: str \| None) -> list[CategoryEntity]` | Yes  |

### New DTOs

| DTO Class               | Type            | Fields                                                    |
| ----------------------- | --------------- | --------------------------------------------------------- |
| `FindCategoryItemResult`| Result (output) | `id`, `collection_id`, `name`, `url_slug`, `created_at`  |
| `FindCategoriesResult`  | Result (output) | `categories: list[FindCategoryItemResult]`                |

> Note: `FindCategoryItemResult` has the same fields as `BaseCategoryResult`. Consider reusing `BaseCategoryResult` and only adding `FindCategoriesResult` to keep the DTO file lean.

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/category/find_categories/`

**`01_success.bru` — Happy Path (no filter):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data` is an array
- [x] Each item has `id`, `collection_id`, `name`, `url_slug`, `created_at`
- [x] `res.body.meta.requestId` is a string

**Error / filter cases:**

- [x] `02_filter_by_collection_id.bru` — Status 200 with `?collection_id=<valid_id>`; array contains only items matching that collection
- [x] `03_invalid_collection_id.bru` — Status 422 when `?collection_id=not-a-uuid`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_categories.py`

**Happy Path:**

- [x] `FindCategoriesUseCase.execute(collection_id=None)` returns all non-deleted categories
- [x] `FindCategoriesUseCase.execute(collection_id=<id>)` returns only categories belonging to that collection

**Edge Cases:**

- [x] Returns an empty list when no categories exist (or none match the filter)

---

## Implementation Checklist

- [x] 1. Domain entity — `CategoryEntity` already exists; no changes needed
- [x] 2. Domain exceptions — none needed
- [x] 3. Repository interface — add `find_all(collection_id: str | None = None) -> list[CategoryEntity]` to `ICategoryRepository`
- [x] 4. DTOs — add `FindCategoryItemResult` and `FindCategoriesResult` to `app/application/dtos/category_dto.py`
- [x] 5. Use case — `app/application/use_cases/category/find_categories.py`
- [x] 6. ORM model — `CategoryModel` already exists; no migration needed
- [x] 7. Mapper — `CategoryMapper` already exists; no changes needed
- [x] 8. Repository implementation — add `find_all(collection_id)` to `CategoryRepositoryImpl`
- [x] 9. Exception mapping — none needed
- [x] 10. Error codes — none needed
- [x] 11. Pydantic schemas — add `CategoryListResponse` to `app/presentation/schemas/category_schema.py`
- [x] 12. Route handler — add `GET /categories` route to `app/presentation/api/app_api/v1/category_routes.py`
- [x] 13. Wire in `deps.py` — `ICategoryRepository` / `CategoryRepositoryImpl` already wired; no change needed
- [x] 14. Alembic migration — not required (no schema changes)
- [x] 15. Bruno test files — `bruno/category/find_categories/` (`folder.bru` + `01_success.bru` + `02_filter_by_collection_id.bru` + `03_invalid_collection_id.bru`)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_categories.py`
