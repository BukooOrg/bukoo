# Auth API Set — Reset Password Proposal

## Overview

| Field        | Value             |
| ------------ | ----------------- |
| API Set      | 1. Auth           |
| Use Case     | 9. Reset Password |
| File Index   | 01_09             |
| Access Level | 🌐 Public         |
| Status       | Implemented       |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | POST                              |
| URL    | `/api/app/v1/auth/password/reset` |
| Auth   | None                              |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | Yes      | application/json |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

### Request Body

| Field        | Type   | Required | Constraints                                                                           |
| ------------ | ------ | -------- | ------------------------------------------------------------------------------------- |
| email        | string | Yes      | Valid email format (EmailStr)                                                         |
| otp          | string | Yes      | Non-empty string; 6-digit code issued by forgot password                              |
| new_password | string | Yes      | 8–128 chars; must pass strength rules (upper, lower, digit, special char; not common) |

**Example:**

```json
{
  "email": "user@example.com",
  "otp": "482910",
  "new_password": "NewP@ssw0rd!"
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

| HTTP Status | Error Code           | Condition                                                                   |
| ----------- | -------------------- | --------------------------------------------------------------------------- |
| 401         | INVALID_TOKEN        | Email not registered, no active OTP token found, or OTP hash does not match |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (invalid email format, `new_password` too weak) |

---

## Procedures

1. **Input validation** — Pydantic validates `ResetPasswordRequest`: `email` as `EmailStr`, `otp` as a non-empty `str`, and `new_password` with the same strength validators already defined in `auth_schema.py` (upper, lower, digit, special character, not a common password, min 8 / max 128 chars). FastAPI returns HTTP 422 automatically on failure.

2. **User lookup** — Call `await self._user_repo.find_by_email(cmd.email)`. If the result is `None`, raise `InvalidTokenError()`. Do not reveal whether the email is registered.

3. **Token lookup** — Call `await self._verification_token_repo.find_active_by_user_and_type(user.id, VerificationTokenType.PASSWORD_RESET)`. If the result is `None` (no token, already used, or expired), raise `InvalidTokenError()`.

4. **OTP verification** — Call `self._hasher.verify(cmd.otp, token.token_hash)`. If it returns `False`, raise `InvalidTokenError()`.

5. **Hash new password** — Call `hashed = self._hasher.hash(cmd.new_password)`.

6. **Apply mutation to user** — Call `user.set_password(hashed)`. This updates `_hashed_password` and `_updated_at` on the `UserEntity`.

7. **Persist user** — Call `await self._user_repo.save(user)`. The repository does not commit.

8. **Consume token** — Call `token.mark_used()`. This sets `_used_at` and `_updated_at` on the `VerificationTokenEntity`.

9. **Persist token** — Call `await self._verification_token_repo.save(token)`. The repository does not commit.

10. **Commit** — Call `await self._db_session.commit()` to flush both mutations as a single transaction.

11. **Return** — Return `ResetPasswordResult(message="Password has been reset successfully.")`.

---

## Domain Impact

### Entities Involved

| Entity                    | Access     | Notes                                             |
| ------------------------- | ---------- | ------------------------------------------------- |
| `UserEntity`              | Read/Write | `set_password(hashed)` updates `_hashed_password` |
| `VerificationTokenEntity` | Read/Write | `mark_used()` consumes the OTP token              |

### Repository Methods Required

| Interface                      | Method                              | New?          |
| ------------------------------ | ----------------------------------- | ------------- |
| `IUserRepository`              | `find_by_email(email)`              | No (existing) |
| `IUserRepository`              | `save(user)`                        | No (existing) |
| `IVerificationTokenRepository` | `find_active_by_user_and_type(...)` | No (existing) |
| `IVerificationTokenRepository` | `save(token)`                       | No (existing) |

### New DTOs

| DTO Class              | Type            | Fields                                        |
| ---------------------- | --------------- | --------------------------------------------- |
| `ResetPasswordCommand` | Command (input) | `email: str`, `otp: str`, `new_password: str` |
| `ResetPasswordResult`  | Result (output) | `message: str`                                |

### New Domain Exceptions

_(None — `InvalidTokenError` covers all failure paths)_

### New Error Codes

_(None — `INVALID_TOKEN` already exists in `ErrorCode`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/reset_password/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Password has been reset successfully."`
- [x] `res.body.meta.requestId` is a string
- [x] Subsequent login with `new_password` succeeds

**Error Cases:**

- [x] `02_invalid_otp.bru` — Status 401 when OTP does not match the stored hash → `INVALID_TOKEN`
- [x] `03_unknown_email.bru` — Status 401 when email is not registered → `INVALID_TOKEN`
- [x] `04_no_active_token.bru` — Status 401 when no active reset token exists (expired or already used) → `INVALID_TOKEN`
- [x] `05_weak_password.bru` — Status 422 when `new_password` fails strength rules → `UNPROCESSABLE_ENTITY`
- [x] `06_invalid_email_format.bru` — Status 422 when `email` is not a valid email address → `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_reset_password.py`

**Happy Path:**

- [x] `ResetPasswordUseCase.execute(valid_command)` returns `ResetPasswordResult` with `message="Password has been reset successfully."`
- [x] After execution, `user.hashed_password` reflects the new hash and token `is_used` is `True`

**Error Cases:**

- [x] Raises `InvalidTokenError` when `user_repo.find_by_email` returns `None`
- [x] Raises `InvalidTokenError` when `verification_token_repo.find_active_by_user_and_type` returns `None`
- [x] Raises `InvalidTokenError` when `hasher.verify` returns `False`

**Edge Cases:**

- [x] Token is marked used even when the new password hash equals the old one
- [x] Both user and token are persisted before `commit()` is called

---

## Implementation Checklist

- [x] 1. Domain entity — existing (`UserEntity`, `VerificationTokenEntity`)
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface methods — all existing
- [x] 4. DTOs (`app/application/dtos/auth_dto.py`) — add `ResetPasswordCommand`, `ResetPasswordResult`
- [x] 5. Use case (`app/application/use_cases/auth/reset_password.py`)
- [x] 6. ORM model — none new
- [x] 7. Mapper — none new
- [x] 8. Repository implementation — none new
- [x] 9. Exception mapping — none new
- [x] 10. Error codes — none new
- [x] 11. Pydantic schemas (`app/presentation/schemas/auth_schema.py`) — add `ResetPasswordRequest`, `ResetPasswordResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/auth_routes.py`) — add `POST /password/reset`
- [x] 13. Wire in `deps.py` — no new dependencies required
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files (`bruno/auth/reset_password/` — `folder.bru` + `01_success.bru` through `06_invalid_email_format.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_reset_password.py`)
