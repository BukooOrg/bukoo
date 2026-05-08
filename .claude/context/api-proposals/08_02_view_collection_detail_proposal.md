# Collection API Set — View Collection Detail Proposal

## Overview

| Field        | Value                     |
| ------------ | ------------------------- |
| API Set      | 8. Collection API Set     |
| Use Case     | 2. View Collection Detail |
| File Index   | 08_02                     |
| Access Level | 🌐 Public                 |
| Status       | Approved                  |

---

## Endpoint

| Field  | Value                                     |
| ------ | ----------------------------------------- |
| Method | GET                                       |
| URL    | `/api/app/v1/collections/{collection_id}` |
| Auth   | None                                      |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

| Parameter     | Type          | Description                      |
| ------------- | ------------- | -------------------------------- |
| collection_id | string (UUID) | ID of the collection to retrieve |

### Query Parameters

_None_

### Request Body

_None_

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "01932abc-0000-7000-0000-000000000001",
    "name": "Fiction",
    "url_slug": "fiction",
    "categories": [
      {
        "id": "01932abc-0000-7000-0000-000000000002",
        "collection_id": "01932abc-0000-7000-0000-000000000001",
        "name": "Literary Fiction",
        "url_slug": "literary-fiction",
        "created_at": "2026-01-15T10:30:00Z"
      }
    ],
    "created_at": "2026-01-10T08:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                          |
| ----------- | -------------------- | -------------------------------------------------- |
| 404         | COLLECTION_NOT_FOUND | No collection found with the given `collection_id` |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure                        |

---

## Procedures

1. FastAPI extracts `collection_id` from the path.
2. Call `collection_repo.find_by_id(collection_id)` — returns `CollectionEntity | None`. This is a new method on `ICollectionRepository`; the ORM implementation filters `CollectionModel.deleted_at.is_(None)`. Because `_categories` is eagerly loaded (`lazy="selectin"`), the entity is returned fully populated.
3. If the result is `None`, raise `CollectionNotFoundError(collection_id)`. The exception handler maps this to HTTP 404 with error code `COLLECTION_NOT_FOUND`.
4. Build `ViewCollectionDetailResult` from the entity: map `id`, `name`, `url_slug`, `created_at`, and construct `BaseCategoryResult` for each entry in `entity.c.wategories`.
5. Return `ViewCollectionDetailResult`. No commit is needed — this is a read-only operation.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                             |
| ------------------ | ------ | ------------------------------------------------- |
| `CollectionEntity` | Read   | Eagerly loads `_categories` via `lazy="selectin"` |
| `CategoryEntity`   | Read   | Accessed through `collection.categories`          |

### Repository Methods Required

| Interface               | Method                                            | New? |
| ----------------------- | ------------------------------------------------- | ---- |
| `ICollectionRepository` | `find_by_id(id: str) -> CollectionEntity \| None` | Yes  |

### New DTOs

| DTO Class                     | Type            | Fields                                                 |
| ----------------------------- | --------------- | ------------------------------------------------------ |
| `ViewCollectionDetailCommand` | Input           | collection_id: str                                     |
| `ViewCollectionDetailResult`  | Result (output) | Inherits `BaseCollectionResult` — no new fields needed |

### New Domain Exceptions

| Exception Class           | File                                  | Inherits          |
| ------------------------- | ------------------------------------- | ----------------- |
| `CollectionNotFoundError` | `app/domain/exceptions/collection.py` | `DomainException` |

### New Error Codes

| Constant               | Value                    | Description                           |
| ---------------------- | ------------------------ | ------------------------------------- |
| `COLLECTION_NOT_FOUND` | `"COLLECTION_NOT_FOUND"` | No collection found with the given ID |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/collections/view_collection_detail/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` equals the requested collection ID
- [x] `res.body.data.name` is a non-empty string
- [x] `res.body.data.url_slug` is a non-empty string
- [x] `res.body.data.categories` is an array
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when `collection_id` does not exist → error code `COLLECTION_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_collection_detail.py`

**Happy Path:**

- [x] `ViewCollectionDetailUseCase.execute(valid_id)` returns `ViewCollectionDetailResult` with correct `id`, `name`, `url_slug`, `created_at`, and `categories`
- [x] Returns `ViewCollectionDetailResult` with an empty `categories` list when the collection has no categories

**Error Cases:**

- [x] Raises `CollectionNotFoundError` when `collection_repo.find_by_id` returns `None`
- [x] Raises `CollectionNotFoundError` for a soft-deleted collection (repo returns `None` by default filter)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/collection_entity.py`) — _existing, no changes_
- [x] 2. Domain exceptions (`app/domain/exceptions/collection.py`) — add `CollectionNotFoundError`; export from `__init__.py`
- [x] 3. Repository interface method (`app/domain/repositories/collection_repository.py`) — add `find_by_id`
- [x] 4. DTOs (`app/application/dtos/collection_dto.py`) — add `ViewCollectionDetailCommand` and`ViewCollectionDetailResult`
- [x] 5. Use case (`app/application/use_cases/collection/view_collection_detail.py`) — `ViewCollectionDetailUseCase`
- [x] 6. ORM model — _no changes (existing `CollectionModel`)_
- [x] 7. Mapper — _no changes (existing `CollectionMapper`)_
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/collection_repository_impl.py`) — implement `find_by_id`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `CollectionNotFoundError → 404`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `COLLECTION_NOT_FOUND`
- [x] 11. Pydantic schemas (`app/presentation/schemas/collection_schema.py`) — `CollectionResponse` already covers the shape; no new schema needed
- [x] 12. Route handler (`app/presentation/api/app_api/v1/collection_routes.py`) — add `GET /{collection_id}` handler
- [x] 13. Wire in `deps.py` — _`CollectionRepo` already wired; no changes_
- [x] 14. Alembic migration — _no schema changes_
- [ ] 15. Bruno test files (`bruno/collections/view_collection_detail/` — `folder.bru` + `01_success.bru` + `02_not_found.bru` + `03_deleted_not_found.bru`)
- [ ] 16. Pytest unit tests (`backend/tests/unit/test_view_collection_detail.py`)
