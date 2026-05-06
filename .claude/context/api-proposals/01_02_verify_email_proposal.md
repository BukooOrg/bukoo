# Auth API Set — Verify Email Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 1. Auth         |
| Use Case     | 2. Verify Email |
| File Index   | 01_02           |
| Access Level | 🌐 Public       |
| Status       | Implemented     |

---

## Endpoint

| Field  | Value                           |
| ------ | ------------------------------- |
| Method | POST                            |
| URL    | `/api/app/v1/auth/verify-email` |
| Auth   | None                            |

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

| Field | Type   | Required | Constraints                     |
| ----- | ------ | -------- | ------------------------------- |
| email | string | Yes      | Valid email address (EmailStr)  |
| otp   | string | Yes      | 6-digit OTP code sent via email |

**Example:**

```json
{
  "email": "user@example.com",
  "otp": "483920"
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
    "email": "user@example.com",
    "message": "Email verified successfully"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                            |
| ----------- | ----------------------- | -------------------------------------------------------------------- |
| 401         | `INVALID_TOKEN`         | No active (non-expired, non-used) token found, or OTP does not match |
| 404         | `USER_NOT_FOUND`        | No user account with the given email                                 |
| 409         | `USER_ALREADY_VERIFIED` | User account is already `ACTIVE`                                     |
| 422         | `UNPROCESSABLE_ENTITY`  | Pydantic validation failure (missing / malformed fields)             |

---

## Procedures

1. **Input validation** — FastAPI + Pydantic validates the body automatically. `email` must parse as `EmailStr`; `otp` is a non-empty string. HTTP 422 on failure.

2. **User lookup** — `await user_repo.find_by_email(cmd.email)`. If `None`, raise `UserNotFoundError(cmd.email)` → HTTP 404 `USER_NOT_FOUND`.

3. **Already-verified guard** — If `user.status == UserStatus.ACTIVE`, raise `UserAlreadyVerifiedError(cmd.email)` → HTTP 409 `USER_ALREADY_VERIFIED`.

4. **Token lookup** — `await verification_token_repo.find_active_by_user_and_type(user.id, VerificationTokenType.EMAIL_VERIFY)`. If `None` (no token, or it is expired / already consumed), raise `InvalidTokenError()` → HTTP 401 `INVALID_TOKEN`.

5. **OTP verification** — `hasher.verify(cmd.otp, token.token_hash)`. If `False`, raise `InvalidTokenError()` → HTTP 401 `INVALID_TOKEN`.

6. **Mark token used** — Call `token.mark_used()` (new method: sets `_used_at = datetime.now(UTC)` and `_updated_at`). Persist via `await verification_token_repo.save(token)`.

7. **Activate user** — Call `user.activate()` (existing method: sets `_status = UserStatus.ACTIVE`, updates `_updated_at`). Persist via `await user_repo.save(user)`.

8. **Create credential account** — Construct an `AccountEntity` with `_id=str(uuid7())`, `_user_id=user.id`, `_provider=AuthProvider.CREDENTIAL`, `_open_id=None`, `_encrypted_token=None`, and `_created_at`/`_updated_at` set to `datetime.now(UTC)`. Persist via `await account_repo.save(account)`.

9. **Commit** — `await self._db_session.commit()`. This commits the token update, user activation, and new account atomically.

10. **Return** — `VerifyEmailResult(email=user.email, message="Email verified successfully")`.

---

## Domain Impact

### Entities Involved

| Entity                    | Access       | Notes                                                               |
| ------------------------- | ------------ | ------------------------------------------------------------------- |
| `UserEntity`              | Read / Write | Status transition PENDING → ACTIVE via existing `activate()` method |
| `VerificationTokenEntity` | Read / Write | OTP hash check; consumed via new `mark_used()` method               |
| `AccountEntity`           | Write        | New `AuthProvider.CREDENTIAL` account created on verification       |

### Repository Methods Required

| Interface                      | Method                                        | New?          |
| ------------------------------ | --------------------------------------------- | ------------- |
| `IUserRepository`              | `find_by_email(email)`                        | No (existing) |
| `IUserRepository`              | `save(user)`                                  | No (existing) |
| `IVerificationTokenRepository` | `find_active_by_user_and_type(user_id, type)` | No (existing) |
| `IVerificationTokenRepository` | `save(token)`                                 | No (existing) |
| `IAccountRepository`           | `save(account)`                               | No (existing) |

### Domain Entity Enhancement

| Entity                    | Change                                                                          |
| ------------------------- | ------------------------------------------------------------------------------- |
| `VerificationTokenEntity` | Add `mark_used()` method: sets `_used_at = datetime.now(UTC)` and `_updated_at` |

### New DTOs

| DTO Class            | Type            | Fields                       |
| -------------------- | --------------- | ---------------------------- |
| `VerifyEmailCommand` | Command (input) | `email: str`, `otp: str`     |
| `VerifyEmailResult`  | Result (output) | `email: str`, `message: str` |

### New Domain Exceptions

| Exception Class            | File                            | Inherits          |
| -------------------------- | ------------------------------- | ----------------- |
| `UserAlreadyVerifiedError` | `app/domain/exceptions/auth.py` | `DomainException` |

### New Error Codes

| Constant                | Value                     | Description                                   |
| ----------------------- | ------------------------- | --------------------------------------------- |
| `USER_ALREADY_VERIFIED` | `"USER_ALREADY_VERIFIED"` | User account email is already verified/active |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/verify_email/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.email` equals the registered email
- [x] `res.body.data.message` is `"Email verified successfully"`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_invalid_otp.bru` — Status 401 when OTP is wrong → `INVALID_TOKEN`
- [x] `03_expired_token.bru` — Status 401 when OTP has expired → `INVALID_TOKEN`
- [x] `04_user_not_found.bru` — Status 404 when email doesn't exist → `USER_NOT_FOUND`
- [x] `05_already_verified.bru` — Status 409 when user is already `ACTIVE` → `USER_ALREADY_VERIFIED`
- [x] `06_missing_fields.bru` — Status 422 when `email` or `otp` is absent

### Pytest Unit Tests

**File:** `backend/tests/unit/test_verify_email.py`

**Happy Path:**

- [x] `VerifyEmailUseCase.execute(valid_command)` returns `VerifyEmailResult` with correct `email`
- [x] User `status` transitions to `UserStatus.ACTIVE`
- [x] Token `used_at` is set (non-`None`) after execution
- [x] An `AccountEntity` with `provider == AuthProvider.CREDENTIAL` is saved

**Error Cases:**

- [x] Raises `UserNotFoundError` when email matches no user
- [x] Raises `UserAlreadyVerifiedError` when user is already `ACTIVE`
- [x] Raises `InvalidTokenError` when no active token exists for the user
- [x] Raises `InvalidTokenError` when OTP hash does not match

**Edge Cases:**

- [x] Raises `InvalidTokenError` when a valid OTP is replayed (token already consumed / `used_at` set)

---

## Implementation Checklist

- [x] 1. Domain entity — add `mark_used()` to `VerificationTokenEntity` (`app/domain/entities/verification_token_entity.py`)
- [x] 2. Domain exceptions — add `UserAlreadyVerifiedError` to `app/domain/exceptions/auth.py` and export from `__init__.py`
- [x] 3. Repository interface methods — no changes needed
- [x] 4. DTOs — add `VerifyEmailCommand` and `VerifyEmailResult` to `app/application/dtos/auth_dto.py`
- [x] 5. Use case — `app/application/use_cases/auth/verify_email.py` (`VerifyEmailUseCase`)
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no new methods needed
- [x] 9. Exception mapping — add `UserAlreadyVerifiedError` to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `USER_ALREADY_VERIFIED` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `VerifyEmailRequest` and `VerifyEmailResponse` to `app/presentation/schemas/auth_schema.py`
- [x] 12. Route handler — add `POST /verify-email` to `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 13. Wire in `deps.py` — add `AccountRepo` dependency to the route handler (`AccountRepo` provider already exists)
- [x] 14. Alembic migration — no schema changes (no new table or column)
- [x] 15. Bruno test files — `bruno/auth/verify_email/` (`folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_verify_email.py`
