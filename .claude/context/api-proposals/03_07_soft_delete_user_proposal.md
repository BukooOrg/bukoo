# Admin — User Management — Soft Delete User Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 7. Soft Delete User        |
| File Index   | 03_07                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | DELETE                        |
| URL    | `/api/app/v1/users/{user_id}` |
| Auth   | Bearer token (ADMIN role)     |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                      |
| --------- | ------------- | -------------------------------- |
| user_id   | string (UUID) | ID of the user account to delete |

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
    "message": "User account has been deleted."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                 | Condition                                                       |
| ----------- | -------------------------- | --------------------------------------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`       | Bearer token is missing, expired, or invalid                    |
| 403         | `PERMISSION_DENIED`        | Authenticated user does not have `ADMIN` role                   |
| 404         | `USER_NOT_FOUND`           | No active (non-deleted) user with the given `user_id` exists    |
| 422         | `CANNOT_SOFT_DELETE_ADMIN` | Target user is an admin — admin accounts cannot be soft-deleted |

---

## Procedures

1. **Auth guard:** The `AdminUser` dependency validates the Bearer token (via `JWTService`), checks the blocklist, and confirms `user.role == UserRole.ADMIN`. On failure the dependency raises HTTP 401 or 403 directly — the use case is never reached.

2. **Input validation:** `user_id` is extracted from the path. FastAPI validates it is a non-empty string; no body is expected.

3. **Instantiate use case:** The route handler instantiates `SoftDeleteUserUseCase(db_session=db_session, user_repo=user_repo)` and calls `execute(SoftDeleteUserCommand(user_id=user_id))`.

4. **Existence check:** Call `await self._user_repo.find_by_id(cmd.user_id)`. `find_by_id` filters `deleted_at IS NULL`, so already-deleted users return `None`. If the result is `None`, raise `UserNotFoundError(cmd.user_id)` → HTTP 404 / `USER_NOT_FOUND`.

5. **Role guard:** If `user.role == UserRole.ADMIN`, raise `CannotSoftDeleteAdminError()` → HTTP 422 / `CANNOT_SOFT_DELETE_ADMIN`. Admin accounts are protected from admin-initiated soft-deletion to prevent accidental lockout of privileged accounts.

6. **Mutation:** Call `user.soft_delete()` on the `UserEntity`. This sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)`.

7. **Persist:** Call `await self._user_repo.save(user)`. The repository executes `session.merge(model)` but does not commit.

8. **Commit:** Call `await self._db_session.commit()` in the use case — single unit of work.

9. **Return:** Return `SoftDeleteUserResult(message="User account has been deleted.")`.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                                |
| ------------ | ------------ | ---------------------------------------------------- |
| `UserEntity` | Read / Write | `soft_delete()` sets `_deleted_at` and `_updated_at` |

### Repository Methods Required

| Interface         | Method           | New?          |
| ----------------- | ---------------- | ------------- |
| `IUserRepository` | `find_by_id(id)` | No (existing) |
| `IUserRepository` | `save(user)`     | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields         |
| ----------------------- | --------------- | -------------- |
| `SoftDeleteUserCommand` | Command (input) | `user_id: str` |
| `SoftDeleteUserResult`  | Result (output) | `message: str` |

### New Domain Exceptions

| Exception Class              | File                            | Inherits          |
| ---------------------------- | ------------------------------- | ----------------- |
| `CannotSoftDeleteAdminError` | `app/domain/exceptions/user.py` | `DomainException` |

### New Error Codes

| Constant                   | Value                        | Description                           |
| -------------------------- | ---------------------------- | ------------------------------------- |
| `CANNOT_SOFT_DELETE_ADMIN` | `"CANNOT_SOFT_DELETE_ADMIN"` | Admin accounts cannot be soft-deleted |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_management/07_soft_delete_user/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"User account has been deleted."`
- [x] `res.body.meta.requestId` is a string
- [x] Subsequent `GET /users/{user_id}` returns 404

**Error Cases:**

- [x] `02_user_not_found.bru` — Status 404 when `user_id` does not exist or is already deleted → `USER_NOT_FOUND`
- [x] `03_cannot_delete_admin.bru` — Status 422 when target user has `ADMIN` role → `CANNOT_SOFT_DELETE_ADMIN`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_user.py`

**Happy Path:**

- [x] `SoftDeleteUserUseCase.execute(valid_command)` returns `SoftDeleteUserResult` with `message == "User account has been deleted."`
- [x] After execution, `user.deleted_at` is not `None`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `find_by_id` returns `None`
- [x] Raises `CannotSoftDeleteAdminError` when target user has `role == UserRole.ADMIN`

**Edge Cases:**

- [x] Re-deleting an already-soft-deleted user raises `UserNotFoundError` (because `find_by_id` filters deleted records)

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/user_entity.py`) — existing (`soft_delete()` method already present)
- [x] 2. Domain exceptions (`app/domain/exceptions/user.py`) — add `CannotSoftDeleteAdminError`; export from `__init__.py`
- [x] 3. Repository interface methods (`app/domain/repositories/user_repository.py`) — no new methods needed
- [x] 4. DTOs (`app/application/dtos/user_dto.py`) — add `SoftDeleteUserCommand`, `SoftDeleteUserResult`
- [x] 5. Use case (`app/application/use_cases/user/soft_delete_user.py`) — new file
- [x] 6. ORM model — no change (no schema change)
- [x] 7. Mapper — no change
- [x] 8. Repository implementation — no change
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `CannotSoftDeleteAdminError` → HTTP 422 / `CANNOT_SOFT_DELETE_ADMIN`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `CANNOT_SOFT_DELETE_ADMIN`
- [x] 11. Pydantic schemas (`app/presentation/schemas/user_schema.py`) — add `SoftDeleteUserResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `DELETE /users/{user_id}`
- [x] 13. Wire in `deps.py` — no new providers needed (UserRepo already wired)
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/user_management/07_soft_delete_user/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_soft_delete_user.py`)
