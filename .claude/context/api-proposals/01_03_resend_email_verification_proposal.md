# Auth API Set — Resend Email Verification Proposal

## Overview

| Field        | Value                        |
| ------------ | ---------------------------- |
| API Set      | 1. Auth                      |
| Use Case     | 3. Resend Email Verification |
| File Index   | 01_03                        |
| Access Level | 🌐 Public                    |
| Status       | Implemented                  |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | POST                                   |
| URL    | `/api/app/v1/auth/resend-verification` |
| Auth   | None                                   |

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

| Field | Type   | Required | Constraints                   |
| ----- | ------ | -------- | ----------------------------- |
| email | string | Yes      | Valid email format (EmailStr) |

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
    "email": "customer@example.com",
    "message": "Verification email resent successfully"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code            | Condition                                      |
| ----------- | --------------------- | ---------------------------------------------- |
| 404         | USER_NOT_FOUND        | No user exists for the given email             |
| 409         | USER_ALREADY_VERIFIED | The user's account is already ACTIVE           |
| 422         | UNPROCESSABLE_ENTITY  | Pydantic validation failure (bad email format) |

---

## Procedures

1. **Input validation:** FastAPI validates the request body via `ResendVerificationRequest` (Pydantic). If `email` is not a valid email format, returns HTTP 422 automatically.

2. **User lookup:** Call `user_repo.find_by_email(cmd.email)`. If `None`, raise `UserNotFoundError(cmd.email)` → HTTP 404, `USER_NOT_FOUND`.

3. **Already-verified guard:** If `user.is_active` is `True` (status is `ACTIVE`), raise `UserAlreadyVerifiedError(cmd.email)` → HTTP 409, `USER_ALREADY_VERIFIED`.

4. **Generate OTP:** Generate a 6-digit OTP with `secrets.randbelow(900000) + 100000`. Hash it with `hasher.hash(str(otp))`. Set `expires_at = datetime.now(UTC) + timedelta(minutes=5)`.

5. **Create token:** Construct a new `VerificationTokenEntity` with `_id=str(uuid7())`, `_user_id=user.id`, `_token_hash=token_hash`, `_type=VerificationTokenType.EMAIL_VERIFY`, `_expires_at=expires_at`, plus `_created_at` and `_updated_at` set to `datetime.now(UTC)`.

6. **Persist token:** Call `verification_token_repo.save(token)`. Repository does not commit.

7. **Commit:** Call `await self._db_session.commit()`.

8. **Send email:** Call `email_svc.send_verification_email(to=user.email, otp=str(otp))`. This dispatches the Celery task asynchronously via the `mail` queue.

9. **Return:** Return `ResendVerificationResult(email=user.email, message="Verification email resent successfully")`.

---

## Domain Impact

### Entities Involved

| Entity                    | Access | Notes                                                                                                                                        |
| ------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------- |
| `UserEntity`              | Read   | Looked up by email; `is_active` checked                                                                                                      |
| `VerificationTokenEntity` | Write  | New token created; previous tokens remain but `find_active_by_user_and_type` returns the most recent, so old OTPs are effectively superseded |

### Repository Methods Required

| Interface                      | Method                 | New?          |
| ------------------------------ | ---------------------- | ------------- |
| `IUserRepository`              | `find_by_email(email)` | No (existing) |
| `IVerificationTokenRepository` | `save(token)`          | No (existing) |

### New DTOs

| DTO Class                   | Type            | Fields                       |
| --------------------------- | --------------- | ---------------------------- |
| `ResendVerificationCommand` | Command (input) | `email: str`                 |
| `ResendVerificationResult`  | Result (output) | `email: str`, `message: str` |

_(Add to `app/application/dtos/auth_dto.py`)_

### New Domain Exceptions

_(None — `UserNotFoundError` and `UserAlreadyVerifiedError` already exist in `app/domain/exceptions/auth.py`)_

### New Error Codes

_(None — `USER_NOT_FOUND` and `USER_ALREADY_VERIFIED` already exist in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/resend_email_verification/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.email` equals the submitted email
- [x] `res.body.data.message` equals `"Verification email resent successfully"`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_missing_email.bru` — Status 422 when `email` field is absent → `UNPROCESSABLE_ENTITY`
- [x] `03_invalid_email_format.bru` — Status 422 when `email` is not a valid email format → `UNPROCESSABLE_ENTITY`
- [x] `04_user_not_found.bru` — Status 404 when email is not registered → error code `USER_NOT_FOUND`
- [x] `05_already_verified.bru` — Status 409 when account is already ACTIVE → error code `USER_ALREADY_VERIFIED`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_resend_email_verification.py`

**Happy Path:**

- [x] `ResendEmailVerificationUseCase.execute(valid_command)` returns `ResendVerificationResult` with correct `email` and `message` fields

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_email` returns `None`
- [x] Raises `UserAlreadyVerifiedError` when `user.is_active` is `True`

**Edge Cases:**

- [x] A new `VerificationTokenEntity` is persisted even when a previous unexpired token already exists for the user
- [x] `email_svc.send_verification_email` is called with the correct `to` address and the plain-text OTP string

---

## Implementation Checklist

- [x] 1. Domain entity — no new entity needed
- [x] 2. Domain exceptions — no new exceptions needed
- [x] 3. Repository interface methods — no new methods needed
- [x] 4. DTOs — add `ResendVerificationCommand` and `ResendVerificationResult` to `app/application/dtos/auth_dto.py`
- [x] 5. Use case — `app/application/use_cases/auth/resend_email_verification.py`
- [x] 6. ORM model — no new model needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — no changes needed
- [x] 9. Exception mapping — no new mappings needed (`UserNotFoundError` and `UserAlreadyVerifiedError` already mapped)
- [x] 10. Error codes — no new codes needed
- [x] 11. Pydantic schemas — add `ResendVerificationRequest` and `ResendVerificationResponse` to `app/presentation/schemas/auth_schema.py`
- [x] 12. Route handler — add `POST /resend-verification` to `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 13. Wire in `deps.py` — no new deps needed (all existing: `UserRepo`, `VerificationTokenRepo`, `PasswordHasher`, `EmailNotificationService`, `DbSession`)
- [x] 14. Alembic migration — no schema changes
- [x] 15. Bruno test files — `bruno/auth/resend_email_verification/` (`folder.bru` + `01_success.bru` + `02` through `05` error cases)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_resend_email_verification.py`
