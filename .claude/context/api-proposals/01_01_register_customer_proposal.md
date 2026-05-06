# Auth API Set — Register Customer Account Proposal

## Overview

| Field        | Value                |
| ------------ | -------------------- |
| API Set      | 1. Auth              |
| Use Case     | 1. Register Customer |
| File Index   | 01_01                |
| Access Level | 🌐 Public            |
| Status       | Implemented          |

---

## Endpoint

| Field  | Value                       |
| ------ | --------------------------- |
| Method | POST                        |
| URL    | `/api/app/v1/auth/register` |
| Auth   | None                        |

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

| Field         | Type   | Required | Constraints                                                                                                                                                                           |
| ------------- | ------ | -------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| email         | string | Yes      | Valid email format; max 255 chars                                                                                                                                                     |
| password      | string | Yes      | `min_length=8`, `max_length=128`; inherits `validate_password` from `LoginRequest` (uppercase, lowercase, digit, special char, not common, no "password" substring, ≥ 4 unique chars) |
| full_name     | string | Yes      | Min 2 chars; max 100 chars                                                                                                                                                            |
| date_of_birth | date   | Yes      | ISO 8601 (`YYYY-MM-DD`); must be in the past; age ≥ 5                                                                                                                                 |

> **Schema note:** `RegisterRequest` extends the existing `LoginRequest` in `app/presentation/schemas/auth_schema.py`. Override `password` to set `min_length=8`. Add `full_name` (already in scaffold) and `date_of_birth` fields with a `@field_validator`.

**Example:**

```json
{
  "email": "reader@example.com",
  "password": "Secure@123",
  "full_name": "Ada Lovelace",
  "date_of_birth": "1990-05-15"
}
```

---

## Response

### Success Response

**Status:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "01932abc-d4e5-7f60-a1b2-c3d4e5f6a7b8",
    "email": "reader@example.com",
    "full_name": "Ada Lovelace",
    "status": "pending",
    "created_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                          |
| ----------- | -------------------- | -------------------------------------------------- |
| 409         | USER_ALREADY_EXISTS  | Email is already registered (any status)           |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (field format, length) |

---

## Procedures

1. **[Input validation]** Pydantic `RegisterRequest` validates all fields including password strength (inherited from `LoginRequest.validate_password`) and `date_of_birth` range. If invalid → 422 (FastAPI handles automatically).
2. **[Uniqueness check]** Call `user_repo.exists_by_email(command.email)`. If `True` → raise `UserAlreadyExistsError`.
3. **[Hash password]** Call `password_hasher.hash(command.password)` → `hashed_password: str`.
4. **[Create user entity]** Instantiate `UserEntity(_id=str(uuid7()), _email=command.email, _full_name=command.full_name, _date_of_birth=command.date_of_birth, _hashed_password=hashed_password, _role=UserRole.USER, _status=UserStatus.PENDING)`.
5. **[Persist user]** Call `user_repo.save(user)`. Repository does NOT commit.
6. **[Generate OTP]** Generate a cryptographically random 6-digit OTP (`secrets.randbelow(900000) + 100000`). Hash it via `password_hasher.hash(str(otp))` → `token_hash`. Set `expires_at = now(UTC) + 15 minutes`.
7. **[Create verification token entity]** Instantiate `VerificationTokenEntity(_id=str(uuid7()), _user_id=user.id, _token_hash=token_hash, _type=VerificationTokenType.EMAIL_VERIFY, _expires_at=expires_at)`.
8. **[Persist token]** Call `verification_token_repo.save(token)`. Repository does NOT commit.
9. **[Commit]** Call `await self._db_session.commit()`. Both inserts land in a single transaction.
10. **[Send email]** Dispatch Celery task `send_verification_email.delay(user_id=user.id, email=user.email, otp=str(otp))` to the `mail` queue. Task receives the plaintext OTP; only the hash is stored in the DB.
11. **[Return]** Build and return `RegisterResult(id=user.id, email=user.email, full_name=user.full_name, status=user.status, created_at=user.created_at)`.

---

## Domain Impact

### Entities Involved

| Entity                    | Access | Notes                                                          |
| ------------------------- | ------ | -------------------------------------------------------------- |
| `UserEntity`              | Write  | Created with `status=PENDING`, `role=USER`                     |
| `VerificationTokenEntity` | Write  | **New entity** — shared with 1.2, 1.3, 1.7, 1.8, 1.9 use cases |

### Repository Methods Required

| Interface                      | Method                                        | New?                                        |
| ------------------------------ | --------------------------------------------- | ------------------------------------------- |
| `IUserRepository`              | `exists_by_email(email)`                      | No (existing)                               |
| `IUserRepository`              | `save(user)`                                  | No (existing)                               |
| `IVerificationTokenRepository` | `save(token)`                                 | Yes                                         |
| `IVerificationTokenRepository` | `find_active_by_user_and_type(user_id, type)` | Yes (define interface now; used by 1.2/1.3) |

### New DTOs

| DTO Class         | Type            | Fields                                             |
| ----------------- | --------------- | -------------------------------------------------- |
| `RegisterCommand` | Command (input) | `email`, `password`, `full_name`, `date_of_birth`  |
| `RegisterResult`  | Result (output) | `id`, `email`, `full_name`, `status`, `created_at` |

### New Domain Exceptions

_(None — `UserAlreadyExistsError` already exists in `app/domain/exceptions/auth_errors.py`)_

### New Error Codes

_(None — `USER_ALREADY_EXISTS` already exists in `app/application/errors/error_codes.py`)_

### New Domain Entity

| Entity                    | File                                               | Notes                                                                        |
| ------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------- |
| `VerificationTokenEntity` | `app/domain/entities/verification_token_entity.py` | Fields: `_id`, `_user_id`, `_token_hash`, `_type`, `_expires_at`, `_used_at` |

### New Enums

| Enum                    | File                    | Values                           |
| ----------------------- | ----------------------- | -------------------------------- |
| `VerificationTokenType` | `app/core/constants.py` | `EMAIL_VERIFY`, `PASSWORD_RESET` |

---

## Test Cases

### Bruno Tests

**File:** `bruno/auth/register.bru`

**Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"pending"`
- [x] `res.body.data.email` equals the submitted email
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] Status 422 when `email` is malformed
- [x] Status 422 when `password` is shorter than 8 characters
- [x] Status 422 when `password` has no special character
- [x] Status 422 when `date_of_birth` is in the future
- [x] Status 422 when `date_of_birth` corresponds to age < 5
- [x] Status 409, error code `USER_ALREADY_EXISTS` when email is already registered
- [x] Status 422 when `full_name` is missing

### Pytest Unit Tests

**File:** `backend/tests/unit/test_register_customer.py`

**Happy Path:**

- [x] `RegisterCustomerUseCase.execute(valid_command)` returns `RegisterResult` with `status="pending"` and correct field values
- [x] `user_repo.save` is called once with a `UserEntity` having `role=USER` and `status=PENDING`
- [x] `verification_token_repo.save` is called once with a `VerificationTokenEntity` of type `EMAIL_VERIFY`
- [x] `db_session.commit` is called once
- [x] Celery `send_verification_email.delay` is called with correct `email`

**Error Cases:**

- [x] Raises `UserAlreadyExistsError` when `user_repo.exists_by_email` returns `True`

**Edge Cases:**

- [x] User aged exactly 5 years today is accepted (boundary)
- [x] User aged 4 years + 364 days is rejected
- [x] Password of exactly 8 characters with all required char types is accepted

---

## Implementation Checklist

- [x] 1. Domain entity `VerificationTokenEntity` (`app/domain/entities/verification_token_entity.py`) — **new**
- [x] 2. `VerificationTokenType` enum added to `app/core/constants.py` — **new**
- [x] 3. Repository interface `IVerificationTokenRepository` (`app/domain/repositories/verification_token_repository.py`) — **new**
- [x] 4. DTOs `RegisterCommand` / `RegisterResult` (`app/application/dtos/auth_dtos.py`) — **new**
- [x] 5. Use case `RegisterCustomerUseCase` (`app/application/use_cases/auth/register_customer.py`) — **new**
- [x] 6. ORM model `VerificationTokenModel` (`app/infrastructure/db/models/verification_token_model.py`) — **new table**; import in `backend/migrations/env.py`
- [x] 7. Mapper `VerificationTokenMapper` (`app/infrastructure/db/mappers/verification_token_mapper.py`) — **new**
- [x] 8. Repository implementation `VerificationTokenRepositoryImpl` (`app/infrastructure/db/repositories/verification_token_repository_impl.py`) — **new**
- [x] 9. Pydantic schemas — extend existing `RegisterRequest` in `app/presentation/schemas/auth_schema.py`: override `password` `min_length=8`, add `date_of_birth` with `@field_validator`
- [x] 10. Route handler in `app/presentation/api/app_api/v1/auth_routes.py` — update existing scaffold route
- [x] 11. Wire `IVerificationTokenRepository` in `deps.py` — **new provider + alias**
- [x] 12. Celery task `send_verification_email` (`app/infrastructure/tasks/email_tasks.py`) — **new task**
- [x] 13. **Prompt to generate + apply migration:** `make migrate msg="add verification tokens table"` → review generated file in `backend/migrations/versions/` → `make upgrade`
- [x] 14. Bruno test file (`bruno/auth/register.bru`)
- [x] 15. Pytest unit tests (`backend/tests/unit/test_register_customer.py`)
