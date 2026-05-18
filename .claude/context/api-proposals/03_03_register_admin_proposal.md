# Admin — User Management — Register Admin Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 3. Register Admin          |
| File Index   | 03_03                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/users/admin` |
| Auth   | Bearer token (ADMIN role) |

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

| Field         | Type   | Required | Constraints                                     |
| ------------- | ------ | -------- | ----------------------------------------------- |
| email         | string | Yes      | Valid email format; max 255 chars               |
| password      | string | Yes      | Must pass PasswordStr validator (min 8 chars)   |
| full_name     | string | Yes      | min 2, max 255 chars; stripped of whitespace    |
| date_of_birth | string | No       | ISO 8601 date (YYYY-MM-DD); must be in the past |

**Example:**

```json
{
  "email": "admin.jane@bukoo.com",
  "password": "S3cur3P@ssword",
  "full_name": "Jane Admin",
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
    "id": "01932abc-dead-beef-0000-112233445566",
    "email": "admin.jane@bukoo.com",
    "full_name": "Jane Admin",
    "date_of_birth": "1990-05-15",
    "role": "admin",
    "status": "active",
    "avatar_url": null,
    "have_password": true,
    "last_login_at": null,
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
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
| 401         | `UNAUTHORIZED`        | No Authorization header provided               |
| 401         | `TOKEN_EXPIRED`       | Bearer token is expired                        |
| 401         | `INVALID_TOKEN`       | Bearer token is malformed or signature invalid |
| 403         | `FORBIDDEN`           | Authenticated user does not have `ADMIN` role  |
| 409         | `USER_ALREADY_EXISTS` | An account with the given email already exists |
| 422         | `VALIDATION_ERROR`    | Pydantic validation failure (malformed body)   |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the blocklist in Redis, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure; the use case never sees an invalid caller.

2. **Input validation** — FastAPI validates `RegisterAdminRequest` via Pydantic before the handler runs. `email` is validated as an email format, `password` must satisfy `PasswordStr` (min 8 chars), `full_name` is stripped and must not be blank. Returns HTTP 422 on failure.

3. **Email uniqueness check** — Call `await user_repo.exists_by_email(cmd.email)`. If `True`, raise `UserAlreadyExistsError(cmd.email)`, which maps to HTTP 409 `USER_ALREADY_EXISTS`.

4. **Hash password** — Call `self._hasher.hash(cmd.password)` to produce `hashed_password`.

5. **Construct `UserEntity`** — Instantiate with:
   - `_id=str(uuid7())`
   - `_email=cmd.email`
   - `_full_name=cmd.full_name`
   - `_date_of_birth=cmd.date_of_birth`
   - `_role=UserRole.ADMIN`
   - `_status=UserStatus.ACTIVE` ← no email verification required for admin-created accounts
   - `_hashed_password=hashed_password`
   - `_avatar_url=None`, `_last_login_at=None`, `_deleted_at=None`
   - `_created_at=now`, `_updated_at=now`

6. **Persist user** — Call `await self._user_repo.save(user)`. Repository does NOT commit.

7. **Construct `AccountEntity`** — Instantiate with:
   - `_id=str(uuid7())`
   - `_user_id=user.id`
   - `_provider=AuthProvider.CREDENTIAL`
   - `_open_id=None`, `_encrypted_token=None`
   - `_created_at=now`, `_updated_at=now`

8. **Persist account** — Call `await self._account_repo.save(account)`. Repository does NOT commit.

9. **Commit** — Call `await self._db_session.commit()`. Both `user` and `account` are persisted atomically in one transaction.

10. **Return** — Build and return `RegisterAdminResult` populated from the `UserEntity`.

> **Route ordering note:** `POST /users/admin` must be registered in `user_routes.py` **before** any `GET /users/{user_id}` route, so FastAPI resolves the literal path first and does not capture "admin" as a `user_id` parameter.

---

## Domain Impact

### Entities Involved

| Entity          | Access | Notes                                              |
| --------------- | ------ | -------------------------------------------------- |
| `UserEntity`    | Write  | Created with `UserRole.ADMIN`, `UserStatus.ACTIVE` |
| `AccountEntity` | Write  | Credential provider account linked to new user     |

### Repository Methods Required

| Interface            | Method                   | New?          |
| -------------------- | ------------------------ | ------------- |
| `IUserRepository`    | `exists_by_email(email)` | No (existing) |
| `IUserRepository`    | `save(user)`             | No (existing) |
| `IAccountRepository` | `save(account)`          | No (existing) |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                                                    |
| ---------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `RegisterAdminCommand` | Command (input) | `email: str`, `password: str`, `full_name: str`, `date_of_birth: date \| None`                                                            |
| `RegisterAdminResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

Both go in `app/application/dtos/user_dto.py`.

### New Domain Exceptions

_(None — `UserAlreadyExistsError` already exists in `app/domain/exceptions/auth.py`)_

### New Error Codes

_(None — `ErrorCode.USER_ALREADY_EXISTS` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/admin_user_management/register_admin/`

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.role` equals `"admin"`
- [x] `res.body.data.status` equals `"active"`
- [x] `res.body.data.email` equals the submitted email
- [x] `res.body.meta.requestId` is a string

**Error Cases (one file each):**

- [x] `02_conflict_email_taken.bru` — Status 409 when email already registered → error code `USER_ALREADY_EXISTS`
- [x] `03_validation_missing_fields.bru` — Status 422 when required fields are omitted

### Pytest Unit Tests

**File:** `backend/tests/unit/test_register_admin.py`

**Happy Path:**

- [x] `RegisterAdminUseCase.execute(valid_command)` returns `RegisterAdminResult` with `role == UserRole.ADMIN` and `status == UserStatus.ACTIVE`

**Error Cases:**

- [x] Raises `UserAlreadyExistsError` when `user_repo.exists_by_email` returns `True`

**Edge Cases:**

- [x] `date_of_birth=None` is accepted and stored correctly
- [x] Two distinct UUIDs are generated — one for `UserEntity._id`, one for `AccountEntity._id`

---

## Implementation Checklist

- [x] 1. Domain entity — `UserEntity` already exists; no changes needed
- [x] 2. Domain exceptions — `UserAlreadyExistsError` already exists; no changes needed
- [x] 3. Repository interface methods — all required methods already exist on `IUserRepository` and `IAccountRepository`
- [x] 4. DTOs — add `RegisterAdminCommand` and `RegisterAdminResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case — create `app/application/use_cases/user/register_admin.py` (`RegisterAdminUseCase`)
- [x] 6. ORM model — `UserModel` and `AccountModel` already exist; no new table
- [x] 7. Mapper — `UserMapper` and `AccountMapper` already exist; no changes
- [x] 8. Repository implementation — `UserRepositoryImpl` and `AccountRepositoryImpl` already exist; no changes
- [x] 9. Exception mapping — `UserAlreadyExistsError` already mapped; no changes needed
- [x] 10. Error codes — `USER_ALREADY_EXISTS` already exists; no changes needed
- [x] 11. Pydantic schemas — add `RegisterAdminRequest` to `app/presentation/schemas/user_schema.py`; reuse `UserProfileResponse` for the response
- [x] 12. Route handler — add `POST /admin` to `app/presentation/api/app_api/v1/user_routes.py` (register this route **before** any `/{user_id}` routes)
- [x] 13. Wire in `deps.py` — `AccountRepo` already wired; `AdminUser` already wired; no new providers needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/admin_user_management/register_admin/` — `folder.bru` + `01_success.bru` + 2 error case files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_register_admin.py`
