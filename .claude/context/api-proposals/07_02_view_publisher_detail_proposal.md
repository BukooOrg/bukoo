# Publisher API Set — View Publisher Detail Proposal

## Overview

| Field        | Value                    |
| ------------ | ------------------------ |
| API Set      | 7. Publisher             |
| Use Case     | 2. View Publisher Detail |
| File Index   | 07_02                    |
| Access Level | 🌐 Public                |
| Status       | Implemented              |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | GET                                     |
| URL    | `/api/app/v1/publishers/{publisher_id}` |
| Auth   | None                                    |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

| Parameter    | Type          | Description                       |
| ------------ | ------------- | --------------------------------- |
| publisher_id | string (UUID) | UUIDv7 ID of the target publisher |

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
    "id": "01932abc-dead-beef-0000-111122223333",
    "name": "Macmillan Publishers",
    "website": "https://us.macmillan.com/",
    "createdAt": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code          | Condition                                                              |
| ----------- | ------------------- | ---------------------------------------------------------------------- |
| 404         | PUBLISHER_NOT_FOUND | No publisher with the given `publisher_id` exists (or is soft-deleted) |

---

## Procedures

1. **Lookup** — Call `await self._publisher_repo.find_by_id(cmd.publisher_id)`. The repository filters out soft-deleted records automatically.

2. **Existence check** — If `find_by_id` returns `None`, raise `PublisherNotFoundError(cmd.publisher_id)`. The exception handler maps this to HTTP 404 with error code `PUBLISHER_NOT_FOUND`.

3. **Return** — Build and return `ViewPublisherDetailResult(id=publisher.id, name=publisher.name, website=publisher.website, created_at=publisher.created_at)`.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes              |
| ----------------- | ------ | ------------------ |
| `PublisherEntity` | Read   | Fetched by ID only |

### Repository Methods Required

| Interface              | Method                     | New?          |
| ---------------------- | -------------------------- | ------------- |
| `IPublisherRepository` | `find_by_id(publisher_id)` | No (existing) |

### New DTOs

| DTO Class                    | Type            | Fields                                                                 |
| ---------------------------- | --------------- | ---------------------------------------------------------------------- |
| `ViewPublisherDetailCommand` | Command (input) | `publisher_id: str`                                                    |
| `ViewPublisherDetailResult`  | Result (output) | `id: str`, `name: str`, `website: str \| None`, `created_at: datetime` |

_(Added to existing `app/application/dtos/publisher_dto.py`)_

### New Domain Exceptions

_(None — `PublisherNotFoundError` already exists in `app/domain/exceptions/publisher.py`)_

### New Error Codes

_(None — `PUBLISHER_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/publisher/view_publisher_detail/`

- **`01_success.bru` — Happy Path:**
  - [x] Status 200 OK
  - [x] `res.body.success` is `true`
  - [x] `res.body.data.id` equals the requested publisher ID
  - [x] `res.body.data.name` is a non-empty string
  - [x] `res.body.data.website` is a string or `null`
  - [x] `res.body.data.createdAt` is a valid ISO datetime string
  - [x] `res.body.meta.requestId` is a string

- **`02_not_found.bru`** — Status 404 when a random/non-existent UUID is supplied → error code `PUBLISHER_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_publisher_detail.py`

**Happy Path:**

- [x] `ViewPublisherDetailUseCase.execute(ViewPublisherDetailCommand(publisher_id=existing_id))` returns `ViewPublisherDetailResult` with matching `id`, `name`, `website`, and `created_at`
- [x] `website` is correctly propagated as `None` when the publisher has no website

**Error Cases:**

- [x] Raises `PublisherNotFoundError` when `find_by_id` returns `None`

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/publisher_entity.py`) — existing, no changes
- [x] 2. Domain exceptions (`app/domain/exceptions/publisher.py`) — existing, no changes
- [x] 3. Repository interface (`app/domain/repositories/publisher_repository.py`) — existing `find_by_id`, no new methods
- [x] 4. DTOs (`app/application/dtos/publisher_dto.py`) — add `ViewPublisherDetailCommand`, `ViewPublisherDetailResult`
- [x] 5. Use case (`app/application/use_cases/publisher/view_publisher_detail.py`) — **new file**
- [x] 6. ORM model — existing, no changes
- [x] 7. Mapper — existing, no changes
- [x] 8. Repository implementation — existing `find_by_id`, no new methods
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — existing mapping for `PublisherNotFoundError`, no changes
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — existing `PUBLISHER_NOT_FOUND`, no changes
- [x] 11. Pydantic schemas (`app/presentation/schemas/publisher_schema.py`) — add `ViewPublisherDetailResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/publisher_routes.py`) — add `GET /{publisher_id}` to existing router
- [x] 13. Wire in `deps.py` — `PublisherRepo` already wired from 7.3, no changes
- [x] 14. Alembic migration — not needed
- [x] 15. Bruno test files (`bruno/publisher/view_publisher_detail/` — `folder.bru` + `01_success.bru` + `02_not_found.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_view_publisher_detail.py`)
