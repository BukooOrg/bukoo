# Auth API Set — Forgot Password Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 1. Auth            |
| Use Case     | 7. Forgot Password |
| File Index   | 01_07              |
| Access Level | 🌐 Public          |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                              |
| ------ | ---------------------------------- |
| Method | POST                               |
| URL    | `/api/app/v1/auth/password/forgot` |
| Auth   | None                               |

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

| Field | Type   | Required | Constraints                       |
| ----- | ------ | -------- | --------------------------------- |
| email | string | Yes      | Valid email format, max 254 chars |

**Example:**

```json
{
  "email": "customer@example.com"
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
    "message": "If this email is registered, a password reset code has been sent."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code       | Condition                                      |
| ----------- | ---------------- | ---------------------------------------------- |
| 422         | VALIDATION_ERROR | Pydantic validation failure (bad email format) |

> **Note:** Unregistered and non-ACTIVE accounts (PENDING, SUSPENDED, or any
> future status) intentionally return HTTP 200 with the same generic message
> to prevent user enumeration.

---

## Procedures

1. FastAPI receives `POST /api/app/v1/auth/password/forgot`. No Bearer token required.
2. Pydantic validates `ForgotPasswordRequest`; FastAPI returns HTTP 422 automatically if `email` is absent or malformed.
3. The use case calls `await self._user_repo.find_by_email(cmd.email)`.
4. If no user is found, immediately return `ForgotPasswordResult(message="If this email is registered, a password reset code has been sent.")` without raising an exception — prevents user enumeration.
5. If `user.status != UserStatus.ACTIVE`, return the same generic message without sending an email. This covers PENDING users (registered but email not yet verified — they should use `/auth/resend-verification` instead), SUSPENDED users, and any future non-ACTIVE statuses.
6. Call `await self._verification_token_repo.find_active_by_user_and_type(user.id, VerificationTokenType.PASSWORD_RESET)` to check for a pre-existing active reset token.
7. If an existing active token is found, call `existing_token.mark_used()` then `await self._verification_token_repo.save(existing_token)` to invalidate it before issuing a fresh one.
8. Generate a 6-digit OTP: `otp = secrets.randbelow(900000) + 100000`.
9. Hash the OTP: `token_hash = self._hasher.hash(str(otp))`.
10. Construct a new `VerificationTokenEntity` with `_type=VerificationTokenType.PASSWORD_RESET`, `_expires_at=datetime.now(UTC) + timedelta(minutes=15)`, and `_id=str(uuid7())`.
11. Persist the new token: `await self._verification_token_repo.save(new_token)`.
12. Commit the unit of work: `await self._db_session.commit()`.
13. Dispatch the reset email: `self._email_svc.send_password_reset_email(to=user.email, otp=str(otp))` — the `CeleryEmailNotificationService` implementation enqueues a Celery task internally.
14. Return `ForgotPasswordResult(message="If this email is registered, a password reset code has been sent.")`.

---

## Domain Impact

### Entities Involved

| Entity                    | Access       | Notes                                                  |
| ------------------------- | ------------ | ------------------------------------------------------ |
| `UserEntity`              | Read         | Looked up by email; status checked before proceeding   |
| `VerificationTokenEntity` | Read / Write | Existing active token invalidated; new token persisted |

### Repository Methods Required

| Interface                      | Method                                              | New?          |
| ------------------------------ | --------------------------------------------------- | ------------- |
| `IUserRepository`              | `find_by_email(email)`                              | No (existing) |
| `IVerificationTokenRepository` | `find_active_by_user_and_type(user_id, token_type)` | No (existing) |
| `IVerificationTokenRepository` | `save(token)`                                       | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields         |
| ----------------------- | --------------- | -------------- |
| `ForgotPasswordCommand` | Command (input) | `email: str`   |
| `ForgotPasswordResult`  | Result (output) | `message: str` |

### New Domain Exceptions

_(None — non-ACTIVE and unregistered emails are silently handled to prevent user enumeration.)_

### New Error Codes

_(None — no new domain exceptions are raised.)_

### New Application Interface Method

| Interface                   | Method                                       | New? |
| --------------------------- | -------------------------------------------- | ---- |
| `IEmailNotificationService` | `send_password_reset_email(to, otp) -> None` | Yes  |

Must be declared as an `@abstractmethod` in `app/application/interfaces/email_notification_service.py`
and implemented with `@override` in `CeleryEmailNotificationService` in
`app/infrastructure/tasks/email_notification_service.py`.

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/forgot_password/`

**`01_success.bru` — Happy Path (registered, ACTIVE user):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"If this email is registered, a password reset code has been sent."`
- [x] `res.body.meta.requestId` is a string

**Error / Silent Cases:**

- [x] `02_unregistered_email.bru` — Status 200 OK when email is not in the system (identical response, no enumeration)
- [x] `03_invalid_email_format.bru` — Status 422 when `email` is not a valid email address → error code `VALIDATION_ERROR`
- [x] `04_missing_email_field.bru` — Status 422 when `email` field is absent → error code `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_forgot_password.py`

**Happy Path:**

- [x] `ForgotPasswordUseCase.execute(valid_command)` returns `ForgotPasswordResult` with the generic message and calls `send_password_reset_email` once
- [x] A new `VerificationTokenEntity` is saved with `type == VerificationTokenType.PASSWORD_RESET` and `expires_at` approximately 15 minutes in the future

**Silenced Cases (no exception raised, no email sent):**

- [x] Returns `ForgotPasswordResult` without calling `send_password_reset_email` when user is not found
- [x] Returns `ForgotPasswordResult` without calling `send_password_reset_email` when user status is `UserStatus.PENDING`
- [x] Returns `ForgotPasswordResult` without calling `send_password_reset_email` when user status is `UserStatus.SUSPENDED`

**Edge Cases:**

- [x] No existing active reset token → skip invalidation, proceed to create new token normally
- [x] Existing active reset token present → `mark_used()` is called and the old token is saved before the new token is created

---

## Implementation Checklist

- [x] 1. Domain entity — `VerificationTokenEntity` (existing, no changes)
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface methods — all existing, no changes
- [x] 4. DTOs — add `ForgotPasswordCommand`, `ForgotPasswordResult` to `app/application/dtos/auth_dto.py`
- [x] 5. Application interface — add `send_password_reset_email(to, otp)` abstract method to `app/application/interfaces/email_notification_service.py`; add `@override` implementation to `CeleryEmailNotificationService` in `app/infrastructure/tasks/email_notification_service.py`
- [x] 6. Use case — `app/application/use_cases/auth/forgot_password.py`
- [x] 7. ORM model — none new
- [x] 8. Mapper — none new
- [x] 9. Repository implementation — none new
- [x] 10. Exception mapping — none new
- [x] 11. Error codes — none new
- [x] 12. Pydantic schemas — add `ForgotPasswordRequest`, `ForgotPasswordResponse` to `app/presentation/schemas/auth_schema.py`
- [x] 13. Route handler — add `POST /auth/password/forgot` to `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 14. Wire in `deps.py` — no new providers needed (all existing dependencies)
- [x] 15. Alembic migration — none needed (no schema changes)
- [x] 16. Bruno test files — `bruno/auth/forgot_password/folder.bru` + `01_success.bru`, `02_unregistered_email.bru`, `03_invalid_email_format.bru`, `04_missing_email_field.bru`
- [x] 17. Pytest unit tests — `backend/tests/unit/test_forgot_password.py`
