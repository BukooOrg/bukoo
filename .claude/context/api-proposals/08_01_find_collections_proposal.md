# Collection API Set — Find Collections Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 8. Collection API Set |
| Use Case     | 1. Find Collections   |
| File Index   | 08_01                 |
| Access Level | 🌐 Public             |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | GET                       |
| URL    | `/api/app/v1/collections` |
| Auth   | None                      |

---

## Request

### Headers

_(None required)_

### Path Parameters

_(None)_

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
  "data": [
    {
      "id": "01932abc-def0-7000-a000-000000000001",
      "name": "Fiction",
      "url_slug": "fiction",
      "categories": [
        {
          "id": "01932abc-def0-7000-a000-000000000002",
          "collection_id": "01932abc-def0-7000-a000-000000000001",
          "name": "Literary Fiction",
          "url_slug": "literary-fiction",
          "created_at": "2026-01-10T08:00:00Z"
        }
      ],
      "created_at": "2026-01-10T08:00:00Z"
    }
  ],
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

No domain error cases — this is a public read endpoint. Pydantic/FastAPI still returns 422 on malformed requests, but there are no query parameters or body to validate.

---

## Procedures

1. **No auth guard** — endpoint is public; no `CurrentUser` or `AdminUser` dependency.
2. **Fetch all collections** — use case calls `await self._collection_repo.find_all()`. Returns a `list[CollectionEntity]`. Each `CollectionEntity` has its `_categories` list already selectin-loaded by the ORM (matching the existing `CollectionModel.categories` relationship with `lazy="selectin"`).
3. **Map to DTOs** — for each `CollectionEntity`, construct a `CollectionResult` by mapping each nested `CategoryEntity` to a `CategoryResult` DTO.
4. **Return** — build and return `FindCollectionsResult(collections=[...])`. An empty list is a valid result when no collections exist.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                       |
| ------------------ | ------ | ------------------------------------------- |
| `CollectionEntity` | Read   | Includes selectin-loaded `_categories` list |
| `CategoryEntity`   | Read   | Embedded within each `CollectionEntity`     |

### Repository Methods Required

| Interface               | Method                                 | New? |
| ----------------------- | -------------------------------------- | ---- |
| `ICollectionRepository` | `find_all() -> list[CollectionEntity]` | Yes  |

### New DTOs

To be added to `app/application/dtos/collection_dto.py`:

| DTO Class               | Type            | Fields                                                                                                                       |
| ----------------------- | --------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `CategoryResult`        | Result (output) | `id: str`, `collection_id: str`, `name: str`, `url_slug: str`, `created_at: datetime` (app/application/dtos/category_dto.py) |
| `CollectionResult`      | Result (output) | `id: str`, `name: str`, `url_slug: str`, `created_at: datetime`, `categories: list[CategoryResult]`                          |
| `FindCollectionsResult` | Result (output) | `collections: list[CollectionResult]`                                                                                        |

> **Note:** The existing `CreateCollectionResult.categories` field is typed as `list[object]`. As part of this implementation, update it to `list[CategoryResult]` for consistency. Since 8.3 only ever returns an empty list on creation, this is a safe in-place change.

### New Pydantic Schemas

To be added to `app/presentation/schemas/collection_schema.py`:

| Schema Class                 | Type     | Fields                                                                                                                              |
| ---------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| `CategoryResponse`           | Response | `id: str`, `collection_id: str`, `name: str`, `url_slug: str`, `created_at: datetime` (app/presentation/schemas/category_schema.py) |
| `CollectionListItemResponse` | Response | `id: str`, `name: str`, `url_slug: str`, `categories: list[CategoryResponse]`, `created_at: datetime`                               |

> **Note:** The existing `CollectionResponse.categories` is typed as `list[object]`. Update it to `list[CategoryResponse]` so that all collection responses share the same typed category schema.

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/collection/find_collections/`

**`01_success.bru` — Happy Path** (assumes seed data is present):

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data` is an array
- [x] Each item in `res.body.data` has `id` (string), `name` (string), `url_slug` (string), `created_at` (string), `categories` (array)
- [x] Each item in a collection's `categories` has `id`, `collection_id`, `name`, `url_slug`, `created_at`
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_collections.py`

**Happy Path:**

- [x] `FindCollectionsUseCase.execute()` returns `FindCollectionsResult` with a list of `CollectionResult` objects
- [x] Each `CollectionResult` in the list has correctly mapped `CategoryResult` objects in `categories`

**Edge Cases:**

- [x] Returns `FindCollectionsResult(collections=[])` when the repository returns an empty list
- [x] Categories within each `CollectionResult` preserve the full `CategoryResult` fields (`id`, `collection_id`, `name`, `url_slug`, `created_at`)

---

## Implementation Checklist

- [x] 1. Domain entity — no changes
- [x] 2. Domain exceptions — no new exceptions
- [x] 3. Repository interface (`app/domain/repositories/collection_repository.py`) — add `find_all()` method
- [x] 4. DTOs (`app/application/dtos/collection_dto.py`) — add `CollectionResult`, `FindCollectionsResult`; ; update `CreateCollectionResult.categories` to `list[CategoryResult]` ; (`app/application/dtos/category_dto.py`) - add `CategoryResult`
- [x] 5. Use case (`app/application/use_cases/collection/find_collections.py`) — `FindCollectionsUseCase`
- [x] 6. ORM model — no changes
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/collection_repository_impl.py`) — add `find_all()` method
- [x] 9. Exception mapping — no new exceptions
- [x] 10. Error codes — no new error codes
- [x] 11. Pydantic schemas (`app/presentation/schemas/collection_schema.py`) — add `CollectionListItemResponse`; update `CollectionResponse.categories` to `list[CategoryInCollectionResponse]` ; (`app/presentation/schemas/category_schema.py`) — add `CategoryResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/collection_routes.py`) — add `GET /collections`
- [x] 13. Wire in `deps.py` — `CollectionRepo` alias already exists from 8.3; no changes needed
- [x] 14. Alembic migration — not required
- [x] 15. Bruno test files (`bruno/collection/find_collections/` — `folder.bru` + `01_success.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_find_collections.py`)
