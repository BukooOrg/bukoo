# User Profile — Remove Avatar Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 2. User Profile  |
| Use Case     | 5. Remove Avatar |
| File Index   | 02_05            |
| Access Level | 👤🔑 Both        |
| Status       | Approved         |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | DELETE                        |
| URL    | `/api/app/v1/users/me/avatar` |
| Auth   | Bearer token (any role)       |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

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
  "data": {
    "id": "01932abc-...",
    "email": "user@example.com",
    "fullName": "Jane Doe",
    "dateOfBirth": "1990-05-20",
    "role": "user",
    "status": "active",
    "avatarUrl": null,
    "havePassword": true,
    "lastLoginAt": "2026-01-15T10:00:00Z",
    "createdAt": "2025-06-01T08:00:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                     |
| ----------- | -------------------- | --------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | Bearer token is missing, expired, or revoked  |
| 404         | USER_NOT_FOUND       | Authenticated user no longer exists in the DB |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure                   |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer JWT, checks the revocation blocklist via `RedisCacheService`, and loads the active `UserEntity` for the caller. If the token is missing, expired, or revoked, HTTP 401 is raised before the route handler executes.

2. **Load user:** Call `await self._user_repo.find_by_id(command.user_id)`. If the result is `None`, raise `UserNotFoundError(command.user_id)`.

3. **No-op guard:** If `user.avatar_url is None`, skip to step 8 immediately — deleting a non-existent avatar is not an error (idempotent DELETE).

4. **Capture storage key:** Store `avatar_key = user.avatar_url` before mutating the entity, to use for the storage deletion after commit.

5. **Clear avatar on entity:** Call `user.update_avatar(None)`. This sets `_avatar_url = None` and stamps `_updated_at = datetime.now(UTC)`.

6. **Persist:** Call `await self._user_repo.save(user)`. The repository does not commit.

7. **Commit** — Call `await self._db_session.commit()`. Committing before the storage delete ensures the DB record already reflects the cleared avatar and no broken reference exists if the storage call fails.

8. **Storage delete** — Call `await self._storage_service.delete(avatar_key)`. The storage service's `delete()` must be idempotent — no error is raised if the object is already absent.

9. **Return:** Build and return `RemoveAvatarResult` populated from the updated `UserEntity`.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                                               |
| ------------ | ------------ | ------------------------------------------------------------------- |
| `UserEntity` | Read / Write | `update_avatar(None)` clears `_avatar_url` and stamps `_updated_at` |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### Service Interfaces Required

| Interface         | Method        | New?          |
| ----------------- | ------------- | ------------- |
| `IStorageService` | `delete(key)` | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                                                                    |
| --------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `RemoveAvatarCommand` | Command (input) | `user_id: str`                                                                                                                            |
| `RemoveAvatarResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/remove_avatar/`

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.avatarUrl` is `null`
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_no_auth_header.bru` — Status 401 when no Authorization header provided
- [ ] `03_invalid_token.bru` — Status 401 when token is expired or invalid
- [ ] `04_idempotent.bru` — Status 200 when avatar is already null (idempotent no-op, not an error)

### Pytest Unit Tests

**File:** `backend/tests/unit/test_remove_avatar.py`

**Happy Path:**

- [ ] `RemoveAvatarUseCase.execute(valid_command)` returns `RemoveAvatarResult` with `avatar_url=None` when the user has an existing avatar
- [ ] `storage_service.delete()` is called with the correct `avatar_key` when the user has an avatar

**Error Cases:**

- [ ] Raises `UserNotFoundError` when `user_repo.find_by_id()` returns `None`

**Edge Cases:**

- [ ] When `user.avatar_url` is already `None`, `storage_service.delete()` is never called and the result still has `avatar_url=None`
- [ ] `db_session.commit()` is called before `storage_service.delete()` (commit-first ordering invariant)

---

## Implementation Checklist

- [ ] 1. Domain entity (`app/domain/entities/user_entity.py`) — existing; `update_avatar(None)` already supports clearing
- [ ] 2. Domain exceptions (`app/domain/exceptions/`) — none new
- [ ] 3. Repository interface methods (`app/domain/repositories/`) — none new
- [ ] 4. DTOs (`app/application/dtos/user_dto.py`) — add `RemoveAvatarCommand`, `RemoveAvatarResult`
- [ ] 5. Use case (`app/application/use_cases/user/remove_avatar.py`) — new
- [ ] 6. ORM model — no new table
- [ ] 7. Mapper — no change
- [ ] 8. Repository implementation — no change
- [ ] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — no new entries
- [ ] 10. Error codes (`app/application/errors/error_codes.py`) — no new entries
- [ ] 11. Pydantic schemas (`app/presentation/schemas/user_schema.py`) — add `RemoveAvatarResponse`
- [ ] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `DELETE /users/me/avatar`
- [ ] 13. Wire in `deps.py` — `StorageService` already wired; inject alongside `UserRepo` and `DbSession`
- [ ] 14. Alembic migration — no schema change
- [ ] 15. Bruno test files (`bruno/user_profile/remove_avatar/` — `folder.bru` + `01_success.bru` + one file per error case)
- [ ] 16. Pytest unit tests (`backend/tests/unit/test_remove_avatar.py`)
