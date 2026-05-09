# Auth API Set — Verify Password Reset Proposal

## Overview

| Field        | Value                    |
| ------------ | ------------------------ |
| API Set      | 1. Auth                  |
| Use Case     | 8. Verify Password Reset |
| File Index   | 01_08                    |
| Access Level | 🌐 Public                |
| Status       | Implemented              |

---

## Endpoint

| Field  | Value                                    |
| ------ | ---------------------------------------- |
| Method | GET                                      |
| URL    | `/api/app/v1/auth/password/reset/verify` |
| Auth   | None                                     |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | No       | application/json |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type   | Required | Default | Description                                           |
| --------- | ------ | -------- | ------- | ----------------------------------------------------- |
| email     | string | Yes      | —       | Email address the reset code was sent to              |
| otp       | string | Yes      | —       | 6-digit OTP code received in the password reset email |

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
    "valid": true
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code             | Condition                                                                    |
| ----------- | ---------------------- | ---------------------------------------------------------------------------- |
| 401         | `INVALID_TOKEN`        | User not found, no active reset token exists, or OTP does not match the hash |
| 422         | `UNPROCESSABLE_ENTITY` | Pydantic validation failure (missing or malformed query params)              |

> **Security note:** User-not-found and OTP-mismatch both map to `INVALID_TOKEN` — no enumeration of registered emails.

---

## Procedures

1. **Input validation** — FastAPI/Pydantic parses `email` and `otp` query parameters from the request. If either is missing or malformed, FastAPI returns HTTP 422 automatically.

2. **User lookup** — Call `user_repo.find_by_email(cmd.email)`. If the result is `None`, raise `InvalidTokenError` (silent fail — do not reveal whether the email is registered).

3. **Active token lookup** — Call `verification_token_repo.find_active_by_user_and_type(user.id, VerificationTokenType.PASSWORD_RESET)`. This method returns the most recent non-expired, non-used token of that type, or `None` if no such token exists. If the result is `None`, raise `InvalidTokenError`.

4. **OTP verification** — Call `hasher.verify(cmd.otp, token.token_hash)`. If the result is `False`, raise `InvalidTokenError`.

5. **Return** — Build and return `VerifyPasswordResetResult(valid=True)`. No mutations are made; `commit()` is not called.

---

## Domain Impact

### Entities Involved

| Entity                    | Access | Notes                               |
| ------------------------- | ------ | ----------------------------------- |
| `UserEntity`              | Read   | Looked up by email to get `user.id` |
| `VerificationTokenEntity` | Read   | Active PASSWORD_RESET token checked |

### Repository Methods Required

| Interface                      | Method                                              | New?          |
| ------------------------------ | --------------------------------------------------- | ------------- |
| `IUserRepository`              | `find_by_email(email)`                              | No (existing) |
| `IVerificationTokenRepository` | `find_active_by_user_and_type(user_id, token_type)` | No (existing) |

### New DTOs

| DTO Class                    | Type            | Fields                   |
| ---------------------------- | --------------- | ------------------------ |
| `VerifyPasswordResetCommand` | Command (input) | `email: str`, `otp: str` |
| `VerifyPasswordResetResult`  | Result (output) | `valid: bool`            |

### New Domain Exceptions

_(None — `InvalidTokenError` already exists in `app/domain/exceptions/auth.py` and is already mapped to HTTP 401 / `INVALID_TOKEN`.)_

### New Error Codes

_(None — `INVALID_TOKEN` already exists in `app/application/errors/error_codes.py`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/verify_password_reset/`

| File                           | Scenario                                                              |
| ------------------------------ | --------------------------------------------------------------------- |
| `01_success.bru`               | Valid email + correct OTP → 200, `res.body.data.valid == true`        |
| `02_missing_params.bru`        | No query params → 422 UNPROCESSABLE_ENTITY                            |
| `03_invalid_otp.bru`           | Valid email + wrong OTP → 401 `INVALID_TOKEN`                         |
| `04_unknown_email.bru`         | Unregistered email + any OTP → 401 `INVALID_TOKEN`                    |
| `05_expired_or_used_token.bru` | Correct email but token already used or expired → 401 `INVALID_TOKEN` |

**`01_success.bru` — Happy Path checks:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.valid` is `true`
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_verify_password_reset.py`

**Happy Path:**

- [x] `VerifyPasswordResetUseCase.execute(valid_command)` returns `VerifyPasswordResetResult(valid=True)`

**Error Cases:**

- [x] Raises `InvalidTokenError` when user is not found by email
- [x] Raises `InvalidTokenError` when `find_active_by_user_and_type` returns `None`
- [x] Raises `InvalidTokenError` when `hasher.verify` returns `False` (OTP mismatch)

**Edge Cases:**

- [x] `otp` field is empty string → Pydantic 422 (schema-level, no use case instantiated)
- [x] Correct OTP for a different token type (e.g., EMAIL_VERIFICATION) → `InvalidTokenError` (wrong type, no active PASSWORD_RESET token found)

---

## Implementation Checklist

- [x] 1. Domain entity — _existing: `VerificationTokenEntity`_
- [x] 2. Domain exceptions — _existing: `InvalidTokenError`_
- [x] 3. Repository interface methods — _existing: `find_by_email`, `find_active_by_user_and_type`_
- [x] 4. DTOs — add `VerifyPasswordResetCommand` and `VerifyPasswordResetResult` to `app/application/dtos/auth_dto.py`
- [x] 5. Use case — `app/application/use_cases/auth/verify_password_reset.py`
- [x] 6. ORM model — _no changes_
- [x] 7. Mapper — _no changes_
- [x] 8. Repository implementation — _no changes_
- [x] 9. Exception mapping — _no changes (`InvalidTokenError` already mapped)_
- [x] 10. Error codes — _no changes (`INVALID_TOKEN` already exists)_
- [x] 11. Pydantic schemas — add `VerifyPasswordResetResponse` to `app/presentation/schemas/auth_schema.py`
- [x] 12. Route handler — add `GET /auth/password/reset/verify` to `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 13. Wire in `deps.py` — inject `UserRepo`, `VerificationTokenRepo`, `Hasher` into the use case (all already have typed aliases)
- [x] 14. Alembic migration — _not needed (no schema changes)_
- [x] 15. Bruno test files — `bruno/auth/verify_password_reset/` (`folder.bru` + 5 test files)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_verify_password_reset.py`
