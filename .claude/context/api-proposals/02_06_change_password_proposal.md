# User Profile — Change Password Proposal

## Overview

| Field        | Value                         |
| ------------ | ----------------------------- |
| API Set      | 2. User Profile               |
| Use Case     | 6. Change Password            |
| File Index   | 02_06                         |
| Access Level | 👤🔑 Both authenticated roles |
| Status       | Implemented                   |

---

## Endpoint

| Field  | Value                           |
| ------ | ------------------------------- |
| Method | PATCH                           |
| URL    | `/api/app/v1/users/me/password` |
| Auth   | Bearer token (any role)         |

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

| Field            | Type   | Required | Constraints                                                                                                                               |
| ---------------- | ------ | -------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| current_password | string | Yes      | Non-empty, plain text                                                                                                                     |
| new_password     | string | Yes      | `PasswordStr`: min 8, max 128; uppercase, lowercase, digit, special char; not a common weak password; must differ from `current_password` |

**Example:**

```json
{
  "current_password": "OldP@ssw0rd!",
  "new_password": "N3wSecur3P@ss!"
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
    "message": "Password changed successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                     | Condition                                                                                      |
| ----------- | ------------------------------ | ---------------------------------------------------------------------------------------------- |
| 400         | `CURRENT_PASSWORD_INCORRECT`   | `current_password` does not match the stored hashed password                                   |
| 400         | `PASSWORD_NOT_SET`             | User is OAuth-only (no password set); cannot change a password that was never created          |
| 400         | `NEW_PASSWORD_SAME_AS_CURRENT` | `new_password` is identical (plain-text comparison) to `current_password`                      |
| 401         | `AUTH_TOKEN_INVALID`           | Bearer token missing, expired, or revoked                                                      |
| 422         | `UNPROCESSABLE_ENTITY`         | Pydantic validation failure (e.g., `new_password` too short, missing required character class) |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token (decodes JWT, checks the Redis blocklist, and confirms the user is `ACTIVE`). Returns the authenticated `UserEntity`. No logic in the use case for this step.

2. **Input validation** — FastAPI/Pydantic automatically validates the request body against the `ChangePasswordRequest` schema. `new_password` uses the existing `PasswordStr` annotated type from `app/application/validators/password.py` (min/max length + complexity rules). HTTP 422 is returned automatically on failure.

3. **OAuth-only guard** — The use case calls `user.have_password`. If `False`, the user has no stored password (OAuth-only account) and cannot change it. Raise `PasswordNotSetError` → HTTP 400, error code `PASSWORD_NOT_SET`.

4. **Same-password check** — If `command.current_password == command.new_password` (plain-text comparison), raise `NewPasswordSameAsCurrentError` → HTTP 400, error code `NEW_PASSWORD_SAME_AS_CURRENT`. This check is done before hashing to avoid unnecessary bcrypt work.

5. **Verify current password** — Call `hasher.verify(command.current_password, user.hashed_password)`. If `False`, raise `CurrentPasswordIncorrectError` → HTTP 400, error code `CURRENT_PASSWORD_INCORRECT`.

6. **Hash new password** — Call `hasher.hash(command.new_password)` to produce the new bcrypt hash.

7. **Mutate entity** — Call `user.set_password(new_hashed_password)`. The `set_password` method updates `_hashed_password` and stamps `_updated_at = datetime.now(UTC)` internally.

8. **Persist** — Call `await self._user_repo.save(user)`. The repository does not commit.

9. **Commit** — Call `await self._db_session.commit()` in the use case to complete the transaction.

10. **Return** — Return `ChangePasswordResult(message="Password changed successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                         |
| ------------ | ------ | --------------------------------------------- |
| `UserEntity` | Write  | `set_password()` and `have_password` are used |

### Repository Methods Required

| Interface         | Method           | New?          |
| ----------------- | ---------------- | ------------- |
| `IUserRepository` | `find_by_id(id)` | No (existing) |
| `IUserRepository` | `save(user)`     | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                                                       |
| ----------------------- | --------------- | ------------------------------------------------------------ |
| `ChangePasswordCommand` | Command (input) | `user_id: str`, `current_password: str`, `new_password: str` |
| `ChangePasswordResult`  | Result (output) | `message: str`                                               |

### New Domain Exceptions

| Exception Class                 | File                            | Inherits          |
| ------------------------------- | ------------------------------- | ----------------- |
| `CurrentPasswordIncorrectError` | `app/domain/exceptions/auth.py` | `DomainException` |
| `PasswordNotSetError`           | `app/domain/exceptions/auth.py` | `DomainException` |
| `NewPasswordSameAsCurrentError` | `app/domain/exceptions/auth.py` | `DomainException` |

### New Error Codes

| Constant                       | Value                            | Description                                          |
| ------------------------------ | -------------------------------- | ---------------------------------------------------- |
| `CURRENT_PASSWORD_INCORRECT`   | `"CURRENT_PASSWORD_INCORRECT"`   | Supplied current password does not match stored hash |
| `PASSWORD_NOT_SET`             | `"PASSWORD_NOT_SET"`             | OAuth-only user has no password to change            |
| `NEW_PASSWORD_SAME_AS_CURRENT` | `"NEW_PASSWORD_SAME_AS_CURRENT"` | New password is identical to the current one         |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/change_password/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Password changed successfully."`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_wrong_current_password.bru` — Status 400 when `current_password` is incorrect → error code `CURRENT_PASSWORD_INCORRECT`
- [x] `03_oauth_only_user.bru` — Status 400 when authenticated user has no password (OAuth-only) → error code `PASSWORD_NOT_SET`
- [x] `04_same_password.bru` — Status 400 when `new_password` equals `current_password` → error code `NEW_PASSWORD_SAME_AS_CURRENT`
- [x] `05_weak_new_password.bru` — Status 422 when `new_password` fails complexity validation (e.g., no special character)

### Pytest Unit Tests

**File:** `backend/tests/unit/test_change_password.py`

**Happy Path:**

- [x] `ChangePasswordUseCase.execute(valid_command)` returns `ChangePasswordResult` with `message = "Password changed successfully."`
- [x] `user.set_password()` is called with the new bcrypt hash; `user_repo.save()` and `db_session.commit()` are called exactly once

**Error Cases:**

- [x] Raises `PasswordNotSetError` when `user.have_password` is `False`
- [x] Raises `CurrentPasswordIncorrectError` when `hasher.verify()` returns `False`
- [x] Raises `NewPasswordSameAsCurrentError` when `current_password == new_password`

**Edge Cases:**

- [x] Pydantic rejects `new_password` shorter than 8 characters before the use case runs
- [x] Pydantic rejects `new_password` missing an uppercase letter before the use case runs

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/user_entity.py`) — existing; `set_password()` and `have_password` already present
- [x] 2. Domain exceptions (`app/domain/exceptions/auth.py`) — add `CurrentPasswordIncorrectError`, `PasswordNotSetError`, `NewPasswordSameAsCurrentError`; export from `__init__.py`
- [x] 3. Repository interface methods (`app/domain/repositories/user_repository.py`) — no new methods needed
- [x] 4. DTOs (`app/application/dtos/user_dto.py`) — add `ChangePasswordCommand`, `ChangePasswordResult`
- [x] 5. Use case (`app/application/use_cases/user/change_password.py`) — new `ChangePasswordUseCase`; inject `IUserRepository` and `IPasswordHasher`
- [x] 6. ORM model — no changes (no schema change)
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation — no changes
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add three new entries
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `CURRENT_PASSWORD_INCORRECT`, `PASSWORD_NOT_SET`, `NEW_PASSWORD_SAME_AS_CURRENT`
- [x] 11. Pydantic schemas (`app/presentation/schemas/user_schema.py`) — add `ChangePasswordRequest` (with `PasswordStr` on `new_password`), `ChangePasswordResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `PATCH /users/me/password`
- [x] 13. Wire in `deps.py` — `IPasswordHasher` alias already wired; confirm `PasswordHasher` typed alias exists and reuse it
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/user_profile/change_password/` — `folder.bru` + `01_success.bru` through `05_weak_new_password.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_change_password.py`)
