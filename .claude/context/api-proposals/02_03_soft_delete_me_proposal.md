# User Profile — Soft Delete Me Proposal

## Overview

| Field        | Value             |
| ------------ | ----------------- |
| API Set      | 2. User Profile   |
| Use Case     | 3. Soft Delete Me |
| File Index   | 02_03             |
| Access Level | 👤 Customer       |
| Status       | Implemented       |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | DELETE                   |
| URL    | `/api/app/v1/users/me`   |
| Auth   | Bearer token (USER role) |

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
    "message": "Your account has been deleted."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-06T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code       | Condition                                         |
| ----------- | ---------------- | ------------------------------------------------- |
| 401         | `UNAUTHORIZED`   | No Authorization header provided                  |
| 401         | `TOKEN_EXPIRED`  | Bearer token has expired                          |
| 401         | `INVALID_TOKEN`  | Bearer token is malformed or invalid              |
| 403         | `FORBIDDEN`      | Authenticated user has `ADMIN` role               |
| 404         | `USER_NOT_FOUND` | User no longer exists in DB (defensive race case) |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency validates the Bearer JWT, checks the revocation blocklist via `RedisCacheService`, and loads the active `UserEntity`. Raises HTTP 401 on any token failure. No role check is performed at the route level — role enforcement lives in the use case.

2. **Route handler** declares `CurrentUser` and `RawToken` dependencies. Creates `SoftDeleteMeCommand(user_id=current_user.id, access_token=raw_token)` and calls `SoftDeleteMeUseCase(db_session=db_session, user_repo=user_repo, token_svc=token_svc).execute(command)`.

3. **User lookup** — Use case calls `user = await self._user_repo.find_by_id(command.user_id)`. If `None` is returned (defensive: race between auth guard and use case), raise `UserNotFoundError(command.user_id)`.

3a. **Role check** — If `user.role != UserRole.USER`, raise `CustomerOnlyError`. This ensures the use case enforces customer-only access without relying on a presentation-layer guard.

4. **Domain mutation** — Call `user.soft_delete()`. The entity method sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)`.

5. **Persist** — Call `await self._user_repo.save(user)`. Repository merges the ORM model via `session.merge()` and does NOT commit.

6. **Commit** — Call `await self._db_session.commit()`. DB is committed first so it is the source of truth; token revocation follows.

7. **Revoke token** — Call `await self._token_svc.revoke_token(command.access_token)`. This adds the token's JTI to the Redis blocklist with a TTL equal to the token's remaining lifetime, matching the logout flow. If Redis fails after the commit, passive protection still applies (`find_by_id` filters `deleted_at IS NULL`).

8. **Return** — Return `SoftDeleteMeResult(message="Your account has been deleted.")`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                                                |
| ------------ | ------ | -------------------------------------------------------------------- |
| `UserEntity` | Write  | `soft_delete()` sets `_deleted_at` and `_updated_at`; already exists |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                             |
| --------------------- | --------------- | -------------------------------------------------- |
| `SoftDeleteMeCommand` | Command (input) | `user_id: str`, `token_payload: dict[str, object]` |
| `SoftDeleteMeResult`  | Result (output) | `message: str`                                     |

### New Domain Exceptions

| Exception           | File                             | Condition             |
| ------------------- | -------------------------------- | --------------------- |
| `CustomerOnlyError` | `app/domain/exceptions/admin.py` | User has `ADMIN` role |

### New Error Codes

_(None — `USER_NOT_FOUND` and `FORBIDDEN` already exist in `ErrorCode`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/soft_delete_me/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` is a non-empty string
- [x] `res.body.meta.requestId` is a non-empty string
- [x] Subsequent `GET /api/app/v1/users/me` with the same token returns 401

**Error Cases:**

- [x] `02_no_auth.bru` — Status 401 when no `Authorization` header provided
- [x] `03_invalid_token.bru` — Status 401 when token is expired or malformed
- [x] `04_admin_forbidden.bru` — Status 403 when called with an admin token → error code `FORBIDDEN`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_me.py`

**Happy Path:**

- [x] `SoftDeleteMeUseCase.execute(valid_command)` returns `SoftDeleteMeResult` with a non-empty `message`
- [x] After `execute()`, `user.deleted_at` is not `None` and `user.is_deleted` is `True`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`
- [x] Raises `CustomerOnlyError` when `user.role == UserRole.ADMIN`

**Edge Cases:**

- [x] `user.updated_at` is updated when `soft_delete()` is called

---

## Implementation Checklist

- [x] 1. Domain entity — `UserEntity.soft_delete()` already exists in `app/domain/entities/user_entity.py`; no changes needed
- [x] 2. Domain exceptions — add `CustomerOnlyError` to `app/domain/exceptions/admin.py`; raised by the use case when `user.role != UserRole.USER` (maps to `ErrorCode.FORBIDDEN`)
- [x] 3. Repository interface — no new methods needed (`find_by_id` and `save` already exist in `IUserRepository`)
- [x] 4. Add `SoftDeleteMeCommand` (fields: `user_id`, `access_token`) and `SoftDeleteMeResult` DTOs to `app/application/dtos/user_dto.py`
- [x] 5. Use case: `app/application/use_cases/user/soft_delete_me.py` — inject `ITokenService`; after user lookup raise `CustomerOnlyError` if `user.role != UserRole.USER`; after `db_session.commit()` call `token_svc.revoke_token(command.access_token)`
- [x] 6. ORM model — no new model (existing `UserModel` already uses `SoftDeleteMixin`)
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no new methods needed
- [x] 9. Exception mapping — added `CustomerOnlyError` → 403 `FORBIDDEN` to `exception_mapper.py`
- [x] 10. Error codes — no changes (`USER_NOT_FOUND` and `FORBIDDEN` already in `ErrorCode`)
- [x] 11. Add `SoftDeleteMeResponse` Pydantic schema to `app/presentation/schemas/user_schema.py`
- [x] 12. Add `DELETE /me` handler to `app/presentation/api/app_api/v1/user_routes.py` — declare `CurrentUser` and `RawToken`; pass `raw_token` in command and `token_svc` to use case; no `CustomerUser` guard needed
- [x] 13. No new aliases needed in `deps.py` — `CurrentUser`, `RawToken`, `TokenService`, `UserRepo`, and `DbSession` are all already wired; remove `require_customer()` and `CustomerUser` if added in a previous pass
- [x] 14. Alembic migration — not required (`deleted_at` column already exists on `users` table via `SoftDeleteMixin`)
- [x] 15. Bruno test files: `bruno/user_profile/soft_delete_me/folder.bru` + `01_success.bru` + `02_no_auth.bru` + `03_invalid_token.bru` + `04_admin_forbidden.bru`
- [x] 16. Pytest unit tests: `backend/tests/unit/test_soft_delete_me.py`
