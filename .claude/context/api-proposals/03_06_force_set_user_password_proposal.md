# Admin — User Management — Force Set User Password Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 6. Force Set User Password |
| File Index   | 03_06                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                                        |
| ------ | -------------------------------------------- |
| Method | POST                                         |
| URL    | `/api/app/v1/users/{user_id}/password-reset` |
| Auth   | Bearer token (ADMIN role)                    |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                                  |
| --------- | ------------- | -------------------------------------------- |
| user_id   | string (UUID) | ID of the user whose password is being reset |

### Query Parameters

_(None)_

### Request Body

| Field        | Type   | Required | Constraints          |
| ------------ | ------ | -------- | -------------------- |
| new_password | string | Yes      | Minimum 8 characters |

**Example:**

```json
{
  "new_password": "NewSecurePass123!"
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
    "message": "Password has been reset successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                     | Condition                                                   |
| ----------- | ------------------------------ | ----------------------------------------------------------- |
| 401         | UNAUTHORIZED                   | No Authorization header provided                            |
| 401         | TOKEN_EXPIRED                  | Bearer token is expired                                     |
| 401         | INVALID_TOKEN                  | Bearer token is malformed or invalid                        |
| 403         | ADMIN_ACCESS_REQUIRED          | Authenticated user does not have the ADMIN role             |
| 404         | USER_NOT_FOUND                 | No active (non-deleted) user found for `user_id`            |
| 409         | CANNOT_RESET_ADMIN_PASSWORD    | Target user has the ADMIN role                              |
| 400         | USER_HAS_NO_CREDENTIAL_ACCOUNT | Target user is OAuth-only and has no password to reset      |
| 422         | UNPROCESSABLE_ENTITY           | Pydantic validation failure (e.g. `new_password` too short) |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist via `RedisCacheService`, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. A non-admin token raises HTTP 403 with error code `ADMIN_ACCESS_REQUIRED` before the use case is reached.

2. **Input validation** — FastAPI validates the request body against the Pydantic `ForceSetUserPasswordRequest` schema. `new_password` must be at least 8 characters; any violation returns HTTP 422 automatically.

3. **Existence check** — The use case calls `await self._user_repo.find_by_id(cmd.user_id)`. This query filters `deleted_at IS NULL`, so soft-deleted users are invisible. If the result is `None`, raise `UserNotFoundError(cmd.user_id)` → HTTP 404 `USER_NOT_FOUND`.

4. **Role guard** — If `user.role == UserRole.ADMIN`, raise `CannotResetAdminPasswordError()` → HTTP 409 `CANNOT_RESET_ADMIN_PASSWORD`. Admin-on-admin password resets are prohibited to prevent privilege escalation from a compromised admin account. Self-service password changes for admins go through endpoint 2.6.

5. **Credential account guard** — If `user.have_password` is `False` (i.e. `_hashed_password is None`), the account is OAuth-only and has no credential login path. Raise `UserHasNoCredentialAccountError()` → HTTP 400 `USER_HAS_NO_CREDENTIAL_ACCOUNT`. Silently adding credentials to an OAuth account is a security concern; a dedicated endpoint should handle that flow explicitly.

6. **Hash the new password** — Call `hashed = self._password_hasher.hash(cmd.new_password)` using the injected `IPasswordHasher`. The plain-text password is never stored.

7. **Mutation** — Call `user.set_password(hashed)`. This updates `_hashed_password` and stamps `_updated_at = datetime.now(UTC)` on the entity. No status check is applied — the admin can reset the password of a `PENDING`, `ACTIVE`, or `SUSPENDED` user.

8. **Persist** — Call `await self._user_repo.save(user)`. The repository executes `session.merge(model)` but does **not** commit.

9. **Commit** — Call `await self._db_session.commit()` in the use case to finalise the transaction.

10. **Return** — Return `ForceSetUserPasswordResult(message="Password has been reset successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity     | Access | Notes                                                         |
| ---------- | ------ | ------------------------------------------------------------- |
| UserEntity | Write  | `set_password()` updates `_hashed_password` and `_updated_at` |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### New DTOs

| DTO Class                     | Type            | Fields                              |
| ----------------------------- | --------------- | ----------------------------------- |
| `ForceSetUserPasswordCommand` | Command (input) | `user_id: str`, `new_password: str` |
| `ForceSetUserPasswordResult`  | Result (output) | `message: str`                      |

### New Domain Exceptions

| Exception Class                   | File                            | Inherits          |
| --------------------------------- | ------------------------------- | ----------------- |
| `CannotResetAdminPasswordError`   | `app/domain/exceptions/user.py` | `DomainException` |
| `UserHasNoCredentialAccountError` | `app/domain/exceptions/user.py` | `DomainException` |

### New Error Codes

| Constant                         | Value                              | Description                                      |
| -------------------------------- | ---------------------------------- | ------------------------------------------------ |
| `CANNOT_RESET_ADMIN_PASSWORD`    | `"CANNOT_RESET_ADMIN_PASSWORD"`    | Target user is an admin; reset is not permitted  |
| `USER_HAS_NO_CREDENTIAL_ACCOUNT` | `"USER_HAS_NO_CREDENTIAL_ACCOUNT"` | Target user has no password (OAuth-only account) |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_management/06_force_set_user_password/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Password has been reset successfully."`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_user_not_found.bru` — Status 404 when `user_id` does not match any active user → error code `USER_NOT_FOUND`
- [x] `03_target_is_admin.bru` — Status 409 when target user has ADMIN role → error code `CANNOT_RESET_ADMIN_PASSWORD`
- [x] `04_no_credential_account.bru` — Status 400 when target user is OAuth-only → error code `USER_HAS_NO_CREDENTIAL_ACCOUNT`
- [x] `05_password_too_short.bru` — Status 422 when `new_password` is fewer than 8 characters → error code `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_force_set_user_password.py`

**Happy Path:**

- [x] `ForceSetUserPasswordUseCase.execute(valid_command)` returns `ForceSetUserPasswordResult` with `message == "Password has been reset successfully."`
- [x] After execute, the fake repo's saved user has a non-None `hashed_password` (hashed by the fake hasher)

**Error Cases:**

- [x] Raises `UserNotFoundError` when the repo returns `None` for the given `user_id`
- [x] Raises `CannotResetAdminPasswordError` when the target user has `role == UserRole.ADMIN`
- [x] Raises `UserHasNoCredentialAccountError` when the target user has `hashed_password == None`

**Edge Cases:**

- [x] A `UserStatus.PENDING` user with a credential account can have their password reset without error
- [x] A `UserStatus.SUSPENDED` user with a credential account can have their password reset without error

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/user_entity.py`) — existing; `set_password()` already present
- [x] 2. Domain exceptions (`app/domain/exceptions/user.py`) — add `CannotResetAdminPasswordError` and `UserHasNoCredentialAccountError`; export both from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/user_repository.py`) — no new methods needed
- [x] 4. DTOs (`app/application/dtos/user_dto.py`) — add `ForceSetUserPasswordCommand` and `ForceSetUserPasswordResult`
- [x] 5. Use case (`app/application/use_cases/user/force_set_user_password.py`) — new file
- [x] 6. ORM model — no new model needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — no new methods needed
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `CannotResetAdminPasswordError` → 409 and `UserHasNoCredentialAccountError` → 400
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `CANNOT_RESET_ADMIN_PASSWORD` and `USER_HAS_NO_CREDENTIAL_ACCOUNT`
- [x] 11. Pydantic schemas (`app/presentation/schemas/user_schema.py`) — add `ForceSetUserPasswordRequest` and `ForceSetUserPasswordResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `POST /users/{user_id}/password-reset`
- [x] 13. Wire in `deps.py` — `ForceSetUserPasswordUseCase` needs `DbSession`, `UserRepo`, and `PasswordHasher` (all already wired; no new providers needed)
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/user_management/06_force_set_user_password/` — `folder.bru` + `01_success.bru` + seven error case files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_force_set_user_password.py`)
