# User Profile — Update Profile Proposal

## Overview

| Field        | Value             |
| ------------ | ----------------- |
| API Set      | 2. User Profile   |
| Use Case     | 2. Update Profile |
| File Index   | 02_02             |
| Access Level | 👤🔑 Both         |
| Status       | Implemented       |

---

## Endpoint

| Field  | Value                   |
| ------ | ----------------------- |
| Method | PATCH                   |
| URL    | `/api/app/v1/users/me`  |
| Auth   | Bearer token (any role) |

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

| Field           | Type                    | Required | Constraints                                                  |
| --------------- | ----------------------- | -------- | ------------------------------------------------------------ |
| `full_name`     | string                  | Yes      | 1–255 characters, non-empty after strip                      |
| `date_of_birth` | string (date, ISO 8601) | No       | Must be a valid past date if provided; null clears the field |

**Example:**

```json
{
  "full_name": "Jane Doe",
  "date_of_birth": "1990-06-15"
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
    "id": "01932abc-...",
    "email": "jane@example.com",
    "full_name": "Jane Doe",
    "date_of_birth": "1990-06-15",
    "role": "user",
    "status": "active",
    "avatar_url": null,
    "have_password": true,
    "last_login_at": "2026-05-06T08:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-05-06T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-06T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code         | Condition                                                                                        |
| ----------- | ------------------ | ------------------------------------------------------------------------------------------------ |
| 401         | `UNAUTHORIZED`     | No Authorization header provided                                                                 |
| 401         | `TOKEN_EXPIRED`    | Bearer token has expired                                                                         |
| 401         | `INVALID_TOKEN`    | Bearer token is malformed or invalid                                                             |
| 404         | `USER_NOT_FOUND`   | Authenticated user no longer exists in DB                                                        |
| 422         | `VALIDATION_ERROR` | Pydantic validation failure (e.g. `full_name` is empty, `date_of_birth` is not a valid ISO date) |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer JWT, checks the revocation blocklist via `RedisCacheService`, and loads the active `UserEntity`. Any token failure raises HTTP 401 before the use case runs.

2. **Input validation** — FastAPI passes the request body to `UpdateProfileRequest` (Pydantic). Returns HTTP 422 if `full_name` is missing or fails length constraints, or if `date_of_birth` is not a parseable date.

3. **Route handler** instantiates `UpdateProfileUseCase(db_session=db_session, user_repo=user_repo)` and calls `execute(UpdateProfileCommand(user_id=current_user.id, full_name=body.full_name, date_of_birth=body.date_of_birth))`.

4. **User lookup** — Use case calls `user = await self._user_repo.find_by_id(command.user_id)`. If `None` is returned (user was deleted between the auth guard and the use case), raise `UserNotFoundError(command.user_id)`.

5. **Domain mutation** — Call `user.update_profile(full_name=command.full_name, date_of_birth=command.date_of_birth)`. The entity method updates `_full_name`, `_date_of_birth`, and `_updated_at = datetime.now(UTC)`. Note: `UserEntity.update_profile` currently takes `date_of_birth: date` (non-optional) — its signature must be updated to `date_of_birth: date | None` to support clearing the field.

6. **Persist** — Call `await self._user_repo.save(user)`. Repository merges the ORM model via `session.merge()` but does NOT commit.

7. **Commit** — Call `await self._db_session.commit()`.

8. **Return** — Build and return `UpdateProfileResult` from the mutated `user` entity fields.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                                      |
| ------------ | ------ | ---------------------------------------------------------- | ----------------------- |
| `UserEntity` | Write  | `update_profile()` method is called; signature needs `date | None`for`date_of_birth` |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                                                    |
| ---------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `UpdateProfileCommand` | Command (input) | `user_id: str`, `full_name: str`, `date_of_birth: date \| None`                                                                           |
| `UpdateProfileResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — `UserNotFoundError` in `app/domain/exceptions/auth.py` covers the only non-validation failure path.)_

### New Error Codes

_(None — `USER_NOT_FOUND` already exists in `ErrorCode`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/update_profile/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.full_name` equals the submitted value
- [x] `res.body.data.date_of_birth` equals the submitted date
- [x] `res.body.data.updated_at` is later than the previous `updated_at`
- [x] `res.body.meta.requestId` is a non-empty string

**Error Cases:**

- [x] `02_no_auth.bru` — Status 401 when no `Authorization` header is provided
- [x] `03_invalid_token.bru` — Status 401 when token is expired or malformed
- [x] `04_empty_full_name.bru` — Status 422 when `full_name` is an empty string → error code `VALIDATION_ERROR`
- [x] `05_invalid_date.bru` — Status 422 when `date_of_birth` is not a valid ISO 8601 date → error code `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_profile.py`

**Happy Path:**

- [x] `UpdateProfileUseCase.execute(valid_command)` returns `UpdateProfileResult` with `full_name` and `date_of_birth` matching the command
- [x] Returned `updated_at` is later than the entity's original `updated_at`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`

**Edge Cases:**

- [x] `date_of_birth=None` clears the field — result `date_of_birth` is `None`
- [x] `full_name` with leading/trailing whitespace is handled by Pydantic before reaching the use case

---

## Implementation Checklist

- [x] 1. Update `UserEntity.update_profile()` signature in `app/domain/entities/user_entity.py` to accept `date_of_birth: date | None`
- [x] 2. Domain exceptions — no new exceptions needed
- [x] 3. Repository interface — no new methods needed
- [x] 4. Add `UpdateProfileCommand` and `UpdateProfileResult` DTOs to `app/application/dtos/` (new file `user_dto.py`)
- [x] 5. Use case: `app/application/use_cases/user/update_profile.py`
- [x] 6. ORM model — no new model (existing `UserModel`)
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no new methods
- [x] 9. Exception mapping — no changes (`UserNotFoundError` already mapped)
- [x] 10. Error codes — no changes
- [x] 11. Add `UpdateProfileRequest` Pydantic schema to `app/presentation/schemas/user_schema.py`; reuse `UserProfileResponse` for the response model
- [x] 12. Add `PATCH /me` handler to `app/presentation/api/app_api/v1/user_routes.py`
- [x] 13. Wire `UpdateProfileUseCase` + `UserRepo` + `DbSession` in `app/presentation/dependencies/deps.py`
- [x] 14. Alembic migration — not required (no schema changes)
- [x] 15. Bruno test files: `bruno/user_profile/update_profile/folder.bru` + `01_success.bru` through `05_invalid_date.bru`
- [x] 16. Pytest unit tests: `backend/tests/unit/test_update_profile.py`
