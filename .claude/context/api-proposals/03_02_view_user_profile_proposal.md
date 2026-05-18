# Admin — User Management — View User Profile Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 2. View User Profile       |
| File Index   | 03_02                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | GET                           |
| URL    | `/api/app/v1/users/{user_id}` |
| Auth   | Bearer token (ADMIN role)     |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | No       | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description               |
| --------- | ------------- | ------------------------- |
| user_id   | string (UUID) | ID of the user to look up |

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
    "id": "01932abc-dead-beef-0000-112233445566",
    "email": "jane.customer@example.com",
    "full_name": "Jane Customer",
    "date_of_birth": "1995-08-20",
    "role": "user",
    "status": "active",
    "avatar_url": null,
    "have_password": true,
    "last_login_at": "2026-05-10T08:45:00Z",
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-05-10T08:45:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-18T12:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code         | Condition                                      |
| ----------- | ------------------ | ---------------------------------------------- |
| 401         | `UNAUTHORIZED`     | No Authorization header provided               |
| 401         | `TOKEN_EXPIRED`    | Bearer token is expired                        |
| 401         | `INVALID_TOKEN`    | Bearer token is malformed or signature invalid |
| 403         | `FORBIDDEN`        | Authenticated user does not have `ADMIN` role  |
| 404         | `USER_NOT_FOUND`   | No non-deleted user exists with the given ID   |
| 422         | `VALIDATION_ERROR` | Pydantic validation failure (malformed path)   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the Redis blocklist, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. Returns HTTP 401 or 403 on failure; the use case never sees an unauthenticated or unauthorized caller.

2. **User lookup** — Call `await self._user_repo.find_by_id(cmd.user_id)`. This filters `deleted_at IS NULL` by default, so soft-deleted users are not visible. If the result is `None`, raise `UserNotFoundError(cmd.user_id)`, which maps to HTTP 404 `USER_NOT_FOUND`.

3. **Return** — Build and return `ViewUserProfileResult` populated from the `UserEntity`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                                                            |
| ------------ | ------ | -------------------------------------------------------------------------------- |
| `UserEntity` | Read   | Includes eagerly loaded `_accounts` and `_address` (selectin-loaded on ORM side) |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                                                                                                                                    |
| ------------------------ | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `ViewUserProfileCommand` | Query (input)   | `user_id: str`                                                                                                                            |
| `ViewUserProfileResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

Both go in `app/application/dtos/user_dto.py`.

### New Domain Exceptions

_(None — `UserNotFoundError` already exists in `app/domain/exceptions/auth.py`)_

### New Error Codes

_(None — `ErrorCode.USER_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/admin_user_management/view_user_profile/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` matches the requested `user_id`
- [x] `res.body.data.email` is a string
- [x] `res.body.data.role` is one of `"user"` or `"admin"`
- [x] `res.body.meta.requestId` is a string

**Error Cases (one file each):**

- [x] `02_not_found.bru` — Status 404 when `user_id` does not exist → error code `USER_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_user_profile.py`

**Happy Path:**

- [x] `ViewUserProfileUseCase.execute(cmd)` returns `ViewUserProfileResult` with `id` matching the queried user

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`

**Edge Cases:**

- [x] Soft-deleted user (returned as `None` by `find_by_id`) correctly raises `UserNotFoundError`

---

## Implementation Checklist

- [x] 1. Domain entity — `UserEntity` already exists; no changes needed
- [x] 2. Domain exceptions — `UserNotFoundError` already exists; no changes needed
- [x] 3. Repository interface methods — `find_by_id` already exists on `IUserRepository`; no changes needed
- [x] 4. DTOs — add `ViewUserProfileCommand` and `ViewUserProfileResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case — create `app/application/use_cases/user/view_user_profile.py` (`ViewUserProfileUseCase`)
- [x] 6. ORM model — `UserModel` already exists; no new table
- [x] 7. Mapper — `UserMapper` already exists; no changes
- [x] 8. Repository implementation — `UserRepositoryImpl` already exists; no changes
- [x] 9. Exception mapping — `UserNotFoundError` already mapped; no changes needed
- [x] 10. Error codes — `USER_NOT_FOUND` already exists; no changes needed
- [x] 11. Pydantic schemas — reuse `UserProfileResponse` from `app/presentation/schemas/user_schema.py` for the response; no new request schema needed (path param only)
- [x] 12. Route handler — add `GET /{user_id}` to `app/presentation/api/app_api/v1/user_routes.py`; register **after** `POST /admin` (3.3) and any future literal-path GET routes to prevent `"admin"` being captured as a `user_id`
- [x] 13. Wire in `deps.py` — `UserRepo` and `AdminUser` already wired; no new providers needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/admin_user_management/view_user_profile/` — `folder.bru` + `01_success.bru` + 1 error case files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_view_user_profile.py`
