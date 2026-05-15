# Publisher API Set — Update Publisher Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 7. Publisher        |
| Use Case     | 4. Update Publisher |
| File Index   | 07_04               |
| Access Level | 🔑 Admin            |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | PATCH                                   |
| URL    | `/api/app/v1/publishers/{publisher_id}` |
| Auth   | Bearer token (ADMIN role)               |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter    | Type          | Description                          |
| ------------ | ------------- | ------------------------------------ |
| publisher_id | string (UUID) | UUIDv7 ID of the publisher to update |

### Query Parameters

_(None)_

### Request Body

| Field   | Type           | Required | Constraints                                               |
| ------- | -------------- | -------- | --------------------------------------------------------- |
| name    | string         | Yes      | 2–255 characters; stripped of leading/trailing whitespace |
| website | string \| null | No       | Valid URL; max 500 characters; `null` clears the website  |

**Example:**

```json
{
  "name": "Macmillan Publishers",
  "website": "https://us.macmillan.com/"
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

| HTTP Status | Error Code            | Condition                                                              |
| ----------- | --------------------- | ---------------------------------------------------------------------- |
| 401         | UNAUTHORIZED          | No Authorization header provided                                       |
| 401         | TOKEN_EXPIRED         | Bearer token is expired                                                |
| 401         | INVALID_TOKEN         | Bearer token is invalid or malformed                                   |
| 403         | ADMIN_ACCESS_REQUIRED | Authenticated user does not have ADMIN role                            |
| 404         | PUBLISHER_NOT_FOUND   | No publisher with the given `publisher_id` exists (or is soft-deleted) |
| 422         | UNPROCESSABLE_ENTITY  | Pydantic validation failure (missing name, name too short, etc.)       |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist via `RedisCacheService`, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure; the use case never runs.

2. **Input validation** — FastAPI/Pydantic validates the request body against `UpdatePublisherRequest`. If `name` is missing, blank after strip, or outside [2, 255] characters, Pydantic raises HTTP 422 automatically. If `website` is provided it is validated as a URL with max 500 characters.

3. **Lookup** — Call `await self._publisher_repo.find_by_id(cmd.publisher_id)`. The repository filters out soft-deleted records.

4. **Existence check** — If `find_by_id` returns `None`, raise `PublisherNotFoundError(cmd.publisher_id)`. The exception handler maps this to HTTP 404 with error code `PUBLISHER_NOT_FOUND`.

5. **Mutation** — Call `publisher.update(name=cmd.name, website=cmd.website)`. The entity method updates `_name`, `_website`, and sets `_updated_at = datetime.now(UTC)` internally.

6. **Persist** — Call `await self._publisher_repo.save(publisher)`. The repository calls `session.merge(model)` but does not commit.

7. **Commit** — Call `await self._db_session.commit()` to finalise the transaction.

8. **Return** — Build and return `UpdatePublisherResult(id=publisher.id, name=publisher.name, website=publisher.website, created_at=publisher.created_at)`.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                         |
| ----------------- | ------ | --------------------------------------------- |
| `PublisherEntity` | Write  | Mutated via `publisher.update(name, website)` |

### Repository Methods Required

| Interface              | Method                     | New?          |
| ---------------------- | -------------------------- | ------------- |
| `IPublisherRepository` | `find_by_id(publisher_id)` | No (existing) |
| `IPublisherRepository` | `save(publisher)`          | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                                                                 |
| ------------------------ | --------------- | ---------------------------------------------------------------------- |
| `UpdatePublisherCommand` | Command (input) | `publisher_id: str`, `name: str`, `website: str \| None`               |
| `UpdatePublisherResult`  | Result (output) | `id: str`, `name: str`, `website: str \| None`, `created_at: datetime` |

_(Added to existing `app/application/dtos/publisher_dto.py`)_

### New Domain Exceptions

_(None — `PublisherNotFoundError` already exists)_

### New Error Codes

_(None — `PUBLISHER_NOT_FOUND` already exists)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/publisher/update_publisher/`

- **`01_success.bru` — Happy Path (name + website):**
  - [ ] Status 200 OK
  - [ ] `res.body.success` is `true`
  - [ ] `res.body.data.id` equals the path `publisher_id`
  - [ ] `res.body.data.name` equals the submitted name
  - [ ] `res.body.data.website` equals the submitted website
  - [ ] `res.body.data.createdAt` is a valid ISO datetime string
  - [ ] `res.body.meta.requestId` is a string

- **`02_success_clear_website.bru` — Happy Path (website set to null):**
  - [ ] Status 200 OK
  - [ ] `res.body.data.website` is `null`

- **`03_forbidden_non_admin.bru`** — Status 403 when authenticated as a USER-role account → error code `ADMIN_ACCESS_REQUIRED`

- **`04_not_found.bru`** — Status 404 when `publisher_id` does not exist → error code `PUBLISHER_NOT_FOUND`

- **`05_validation_missing_name.bru`** — Status 422 when `name` is omitted

- **`06_validation_blank_name.bru`** — Status 422 when `name` is empty or whitespace-only

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_publisher.py`

**Happy Path:**

- [x] `UpdatePublisherUseCase.execute(UpdatePublisherCommand(publisher_id=existing_id, name="New Name", website="https://example.com"))` returns `UpdatePublisherResult` with the updated `name` and `website`
- [x] Passing `website=None` returns `UpdatePublisherResult` with `website=None` (website cleared)

**Error Cases:**

- [x] Raises `PublisherNotFoundError` when `find_by_id` returns `None`

**Edge Cases:**

- [x] Submitting the same `name` and `website` as the existing values still succeeds (idempotent update)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/publisher_entity.py`) — existing, `update()` method already present
- [x] 2. Domain exceptions (`app/domain/exceptions/publisher.py`) — existing, no changes
- [x] 3. Repository interface (`app/domain/repositories/publisher_repository.py`) — existing `find_by_id` + `save`, no new methods
- [x] 4. DTOs (`app/application/dtos/publisher_dto.py`) — add `UpdatePublisherCommand`, `UpdatePublisherResult`
- [x] 5. Use case (`app/application/use_cases/publisher/update_publisher.py`) — **new file**
- [x] 6. ORM model — existing, no changes
- [x] 7. Mapper — existing, no changes
- [x] 8. Repository implementation — existing `find_by_id` + `save`, no changes
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — existing mapping for `PublisherNotFoundError`, no changes
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — existing `PUBLISHER_NOT_FOUND`, no changes
- [x] 11. Pydantic schemas (`app/presentation/schemas/publisher_schema.py`) — add `UpdatePublisherRequest`, `UpdatePublisherResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/publisher_routes.py`) — add `PATCH /{publisher_id}` to existing router
- [x] 13. Wire in `deps.py` — `PublisherRepo` already wired, no changes
- [x] 14. Alembic migration — not needed
- [x] 15. Bruno test files (`bruno/publisher/update_publisher/` — `folder.bru` + `01_success.bru` through `06_validation_blank_name.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_publisher.py`)
