# Admin — User Management — Activate User Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 5. Activate User           |
| File Index   | 03_05                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | PATCH                                  |
| URL    | `/api/app/v1/users/{user_id}/activate` |
| Auth   | Bearer token (ADMIN role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                    |
| --------- | ------------- | ------------------------------ |
| user_id   | string (UUID) | ID of the user to be activated |

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
    "lastLoginAt": "2026-05-10T08:00:00Z",
    "createdAt": "2026-01-01T00:00:00Z",
    "updatedAt": "2026-05-18T12:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-18T12:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                     | Condition                                                    |
| ----------- | ------------------------------ | ------------------------------------------------------------ |
| 401         | `UNAUTHORIZED`                 | No Authorization header provided                             |
| 401         | `TOKEN_EXPIRED`                | Bearer token is expired                                      |
| 401         | `INVALID_TOKEN`                | Bearer token is malformed or invalid                         |
| 403         | `FORBIDDEN`                    | Authenticated user does not have ADMIN role                  |
| 404         | `USER_NOT_FOUND`               | No active user exists with the given `user_id`               |
| 409         | `USER_ALREADY_ACTIVE`          | Target user's status is already `ACTIVE`                     |
| 409         | `CANNOT_ACTIVATE_PENDING_USER` | Target user is in `PENDING` status (must verify email first) |
| 422         | `VALIDATION_ERROR`             | Pydantic validation failure (malformed UUID, etc.)           |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, confirms `user.role == UserRole.ADMIN`, and returns the authenticated admin `UserEntity`. Any failure raises HTTP 401/403 before the use case is reached.

2. **Look up the target user** — Call `await self._user_repo.find_by_id(cmd.user_id)`. If it returns `None` (user does not exist or is soft-deleted), raise `UserNotFoundError(cmd.user_id)`.

3. **Enforce domain invariant — already active** — If `user.status == UserStatus.ACTIVE`, raise `UserAlreadyActiveError(user.id)`.

4. **Enforce domain invariant — cannot activate a pending user** — If `user.status == UserStatus.PENDING`, raise `CannotActivatePendingUserError()`. A PENDING user must complete email verification through the standard auth flow; an admin cannot bypass that step.

5. **Mutate** — Call `user.activate()`, which sets `_status = UserStatus.ACTIVE` and updates `_updated_at`.

6. **Persist** — Call `await self._user_repo.save(user)`. The repository does NOT commit.

7. **Commit** — Call `await self._db_session.commit()`.

8. **Return** — Build and return `ActivateUserResult` populated from the mutated `UserEntity`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                            |
| ------------ | ------ | ------------------------------------------------ |
| `UserEntity` | Write  | `activate()` method already exists on the entity |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                                                                    |
| --------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `ActivateUserCommand` | Command (input) | `user_id: str`                                                                                                                            |
| `ActivateUserResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

### New Domain Exceptions

| Exception Class                  | File                            | Inherits          |
| -------------------------------- | ------------------------------- | ----------------- |
| `UserAlreadyActiveError`         | `app/domain/exceptions/user.py` | `DomainException` |
| `CannotActivatePendingUserError` | `app/domain/exceptions/user.py` | `DomainException` |

### New Error Codes

| Constant                       | Value                            | Description                                        |
| ------------------------------ | -------------------------------- | -------------------------------------------------- |
| `USER_ALREADY_ACTIVE`          | `"USER_ALREADY_ACTIVE"`          | Target user is already in ACTIVE status            |
| `CANNOT_ACTIVATE_PENDING_USER` | `"CANNOT_ACTIVATE_PENDING_USER"` | PENDING users must activate via email verification |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_management/05_activate_user/`

| File                             | Scenario                                    |
| -------------------------------- | ------------------------------------------- |
| `01_success.bru`                 | Happy path — activate a SUSPENDED user      |
| `02_user_not_found.bru`          | Status 404 → `USER_NOT_FOUND`               |
| `03_already_active.bru`          | Status 409 → `USER_ALREADY_ACTIVE`          |
| `04_cannot_activate_pending.bru` | Status 409 → `CANNOT_ACTIVATE_PENDING_USER` |

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"active"`
- [x] `res.body.data.id` matches the path param
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_activate_user.py`

**Happy Path:**

- [x] `ActivateUserUseCase.execute(ActivateUserCommand(user_id=...))` returns `ActivateUserResult` with `status == UserStatus.ACTIVE`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `find_by_id` returns `None`
- [x] Raises `UserAlreadyActiveError` when user status is already `ACTIVE`
- [x] Raises `CannotActivatePendingUserError` when user status is `PENDING`

**Edge Cases:**

- [x] `user.updated_at` is changed after `activate()` is called
- [x] `save()` is called exactly once on success and not called when a domain exception is raised

---

## Implementation Checklist

- [x] 1. Domain entity — `UserEntity.activate()` already exists; no changes needed
- [x] 2. Domain exceptions — add `UserAlreadyActiveError` and `CannotActivatePendingUserError` to `app/domain/exceptions/user.py`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface — no new methods (`find_by_id` + `save` are sufficient)
- [x] 4. DTOs — add `ActivateUserCommand` and `ActivateUserResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case — `app/application/use_cases/user/activate_user.py`
- [x] 6. ORM model — no new table
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation — no new methods
- [x] 9. Exception mapping — add `UserAlreadyActiveError` and `CannotActivatePendingUserError` to `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `USER_ALREADY_ACTIVE` and `CANNOT_ACTIVATE_PENDING_USER` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — reused existing `UserProfileResponse` (no new schema needed)
- [x] 12. Route handler — add `PATCH /users/{user_id}/activate` to `app/presentation/api/app_api/v1/user_routes.py`
- [x] 13. Wire in `deps.py` — `UserRepo` alias already exists; no new provider needed
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files — `bruno/user_management/05_activate_user/` (`folder.bru` + 4 test files)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_activate_user.py`
