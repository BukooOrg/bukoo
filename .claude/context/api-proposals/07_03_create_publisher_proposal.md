# Publisher API Set — Create Publisher Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 7. Publisher        |
| Use Case     | 3. Create Publisher |
| File Index   | 07_03               |
| Access Level | 🔑 Admin            |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/publishers`  |
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

| Field   | Type           | Required | Constraints                                               |
| ------- | -------------- | -------- | --------------------------------------------------------- |
| name    | string         | Yes      | 2–255 characters; stripped of leading/trailing whitespace |
| website | string \| null | No       | Valid URL; max 500 characters; null if omitted            |

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

**Status:** 201 Created

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

| HTTP Status | Error Code            | Condition                                                        |
| ----------- | --------------------- | ---------------------------------------------------------------- |
| 401         | UNAUTHORIZED          | No Authorization header provided                                 |
| 401         | TOKEN_EXPIRED         | Bearer token is expired                                          |
| 401         | INVALID_TOKEN         | Bearer token is invalid or malformed                             |
| 403         | ADMIN_ACCESS_REQUIRED | Authenticated user does not have ADMIN role                      |
| 422         | UNPROCESSABLE_ENTITY  | Pydantic validation failure (missing name, name too short, etc.) |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist via `RedisCacheService`, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure; the use case never runs.

2. **Input validation** — FastAPI/Pydantic validates the request body against `CreatePublisherRequest`. If `name` is missing, blank after strip, or outside [2, 255] characters, Pydantic raises HTTP 422 automatically. If `website` is provided it is validated as a URL with max 500 characters.

3. **Construct entity** — Generate a new UUIDv7 id with `str(uuid7())`. Capture `now = datetime.now(UTC)`. Instantiate `PublisherEntity(_id=id, _name=cmd.name, _website=cmd.website, _created_at=now, _updated_at=now)`.

4. **Persist** — Call `await self._publisher_repo.save(publisher)`. The repository calls `session.merge(model)` but does not commit.

5. **Commit** — Call `await self._db_session.commit()` to finalise the transaction.

6. **Return** — Build and return `CreatePublisherResult(id=publisher.id, name=publisher.name, website=publisher.website, created_at=publisher.created_at)`.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                            |
| ----------------- | ------ | -------------------------------- |
| `PublisherEntity` | Write  | New entity created and persisted |

### Repository Methods Required

| Interface              | Method                     | New?          |
| ---------------------- | -------------------------- | ------------- |
| `IPublisherRepository` | `find_by_id(publisher_id)` | No (existing) |
| `IPublisherRepository` | `save(publisher)`          | Yes           |

### New DTOs

| DTO Class                | Type            | Fields                                                                 |
| ------------------------ | --------------- | ---------------------------------------------------------------------- |
| `CreatePublisherCommand` | Command (input) | `name: str`, `website: str \| None`                                    |
| `CreatePublisherResult`  | Result (output) | `id: str`, `name: str`, `website: str \| None`, `created_at: datetime` |

### New Domain Exceptions

_(None — no new domain exceptions needed for this use case)_

### New Error Codes

_(None — no new error codes needed)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/publisher/create_publisher/`

- **`01_success.bru` — Happy Path:**
  - [x] Status 201 Created
  - [x] `res.body.success` is `true`
  - [x] `res.body.data.id` is a non-empty string
  - [x] `res.body.data.name` equals the submitted name
  - [x] `res.body.data.website` equals the submitted website
  - [x] `res.body.data.createdAt` is a valid ISO datetime string
  - [x] `res.body.meta.requestId` is a string

- **`02_success_no_website.bru` — Happy Path (no website):**
  - [x] Status 201 Created
  - [x] `res.body.data.website` is `null`

- **`03_forbidden_non_admin.bru`** — Status 403 when authenticated as a USER-role account → error code `ADMIN_ACCESS_REQUIRED`

- **`04_validation_missing_name.bru`** — Status 422 when `name` is omitted from the body

- **`05_validation_blank_name.bru`** — Status 422 when `name` is empty or whitespace-only

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_publisher.py`

**Happy Path:**

- [x] `CreatePublisherUseCase.execute(CreatePublisherCommand(name="Penguin", website=None))` returns `CreatePublisherResult` with correct `name`, `website=None`, and a non-empty `id`
- [x] `CreatePublisherUseCase.execute(CreatePublisherCommand(name="Penguin", website="https://example.com"))` returns `CreatePublisherResult` with `website` set

**Edge Cases:**

- [x] `name` with surrounding whitespace is stripped before persistence (validated at schema layer; unit test confirms the use case receives clean input)
- [x] Each call generates a distinct `id` (two successive executions produce different UUIDs)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/publisher_entity.py`) — existing, no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/publisher.py`) — existing, no new exceptions
- [x] 3. Repository interface method `save(publisher)` (`app/domain/repositories/publisher_repository.py`) — **new method**
- [x] 4. DTOs (`app/application/dtos/publisher_dto.py`) — `CreatePublisherCommand`, `CreatePublisherResult` — **new file**
- [x] 5. Use case (`app/application/use_cases/publisher/create_publisher.py`) — **new file**
- [x] 6. ORM model (`app/infrastructure/db/models/publisher_model.py`) — existing, no changes needed
- [x] 7. Mapper (`app/infrastructure/db/mappers/publisher_mapper.py`) — existing, verify `to_model` handles `website`
- [x] 8. Repository implementation `save()` (`app/infrastructure/db/repositories/publisher_repository_impl.py`) — **new method**
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — no new exceptions
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — no new codes
- [x] 11. Pydantic schemas (`app/presentation/schemas/publisher_schema.py`) — `CreatePublisherRequest`, `CreatePublisherResponse` — **new file**
- [x] 12. Route handler (`app/presentation/api/app_api/v1/publisher_routes.py`) — **new or extend existing file**
- [x] 13. Wire in `deps.py` — add `PublisherRepo` typed alias and `get_publisher_repository()` provider
- [x] 14. Alembic migration — not needed (table already exists)
- [x] 15. Bruno test files (`bruno/publisher/create_publisher/` — `folder.bru` + `01_success.bru` through `05_validation_blank_name.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_create_publisher.py`)
