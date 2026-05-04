# Auth API Set — Credential Login Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 1. Auth API Set       |
| Use Case     | 1.4. Credential Login |
| File Index   | 01_04                 |
| Access Level | 🌐 Public             |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | POST                     |
| URL    | `/api/app/v1/auth/login` |
| Auth   | None                     |

---

## Request

### Headers

| Header       | Required | Description      |
| ------------ | -------- | ---------------- |
| Content-Type | Yes      | application/json |

### Path Parameters

_None_

### Query Parameters

_None_

### Request Body

| Field    | Type           | Required | Constraints                                                                   |
| -------- | -------------- | -------- | ----------------------------------------------------------------------------- |
| email    | string (email) | Yes      | Valid email format                                                            |
| password | string         | Yes      | min 1, max 128 chars; requires uppercase, lowercase, digit, special character |

**Example:**

```json
{
  "email": "customer@bukoo.my",
  "password": "Secure@123"
}
```

---

## Response

### Success Response

**Status:** 200 OK

The access token is delivered in two ways simultaneously:

1. **Response body** — `data.access_token` in the standard envelope
2. **`HttpOnly` cookie** — `access_token` cookie set on the response (value: `Bearer <token>`)

```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

**Cookie set on response:**

| Attribute  | Value                                        |
| ---------- | -------------------------------------------- |
| Name       | `access_token`                               |
| Value      | `Bearer <token>`                             |
| `HttpOnly` | `true`                                       |
| `Secure`   | `true` in production; `false` in development |
| `SameSite` | `lax`                                        |
| `Max-Age`  | `ACCESS_TOKEN_EXPIRE_MINUTES * 60` (seconds) |
| `Path`     | `/`                                          |

### Error Responses

| HTTP Status | Error Code           | Condition                                                      |
| ----------- | -------------------- | -------------------------------------------------------------- |
| 401         | INVALID_CREDENTIALS  | Email not found, account has no password, or password mismatch |
| 403         | USER_NOT_VERIFIED    | Account exists but status is `PENDING` (email unverified)      |
| 403         | USER_SUSPENDED       | Account status is `SUSPENDED`                                  |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (malformed email, etc.)            |

---

## Procedures

This endpoint is **reimplemented** from the scaffold using the **Factory Method Pattern**. The existing `IAuthStrategy` / `CredentialProvider` approach (Strategy pattern) is replaced by a factory hierarchy: `IAuthProvider` (abstract product) + `IAuthProviderFactory` (abstract creator), with `CredentialAuthProvider` and `CredentialAuthProviderFactory` as the concrete implementations. `LoginUseCase` — the consumer — depends only on `IAuthProviderFactory` and never on any concrete class.

**Factory Method class inventory:**

| Role             | Class                           | Layer / File                                                                    |
| ---------------- | ------------------------------- | ------------------------------------------------------------------------------- |
| Abstract product | `IAuthProvider`                 | `application/interfaces/auth_provider.py` (rename from `IAuthStrategy`)         |
| Concrete product | `CredentialAuthProvider`        | `infrastructure/auth/credential_provider.py` (rename from `CredentialProvider`) |
| Abstract creator | `IAuthProviderFactory`          | `application/interfaces/auth_provider_factory.py` (new)                         |
| Concrete creator | `CredentialAuthProviderFactory` | `infrastructure/auth/credential_provider_factory.py` (new)                      |
| Consumer         | `LoginUseCase`                  | `application/use_cases/auth/login.py` (updated)                                 |

> **Scope note:** `LoginUseCase` also serves endpoint 1.5 (`/auth/login/google`). A `GoogleAuthProvider` and `GoogleAuthProviderFactory` will be added in parallel as part of this refactor so both routes continue to work. The Google login route handler will be updated in the same commit.

1. FastAPI receives `POST /api/app/v1/auth/login` with `LoginRequest` body. Pydantic validates `email` (format) and `password` (character constraints). On failure → HTTP 422.
2. `deps.py` resolves `CredentialAuthProviderFactory` by calling `get_credential_factory(user_repo, hasher)`. The factory is returned typed as `IAuthProviderFactory` (the abstract creator). The route handler receives it via the `CredentialAuthFactory` typed alias and never references the concrete type.
3. The route handler constructs `LoginUseCase(db_session=db_session, factory=factory, token_svc=token_svc)` and calls `execute(LoginCommand(email=body.email, password=body.password))`.
4. `LoginUseCase.execute()` calls `self._factory.create_provider()` — the **factory method call** — which returns a `CredentialAuthProvider` typed as `IAuthProvider`. The use case has zero knowledge of which concrete provider was created.
5. `LoginUseCase` calls `provider.authenticate({"email": command.email, "password": command.password})`, delegating authentication entirely to the returned provider.
6. `CredentialAuthProvider.authenticate()` calls `self._user_repo.find_by_email(email)`. If the result is `None` or `not user.have_password`, raises `InvalidCredentialsError` (HTTP 401 `INVALID_CREDENTIALS`).
7. `CredentialAuthProvider` calls `self._hasher.verify(password, user.hashed_password)`. If the hash does not match, raises `InvalidCredentialsError`.
8. `CredentialAuthProvider` checks `user.status == UserStatus.PENDING`. If true, raises `UserNotVerifiedError(user.email)` (HTTP 403 `USER_NOT_VERIFIED`).
9. `CredentialAuthProvider` checks `user.status == UserStatus.SUSPENDED`. If true, raises `UserSuspendedError(user.email)` (HTTP 403 `USER_SUSPENDED`).
10. `CredentialAuthProvider` calls `user.record_login()` (stamps `_last_login_at` and `_updated_at`) then `await self._user_repo.save(user)`. Repository does not commit.
11. `CredentialAuthProvider` returns `AuthResult(user_id=user.id, email=user.email, is_new_user=False)`.
12. `LoginUseCase` calls `await self._db_session.commit()`, persisting the `record_login()` update as a single unit of work.
13. `LoginUseCase` calls `self._token_svc.create_access_token(result.user_id)` and returns `TokenDTO(access_token=token, token_type="bearer")`.
14. The route handler calls `set_auth_cookie(response, result.access_token)` from `app/core/util.py` to attach the `HttpOnly` cookie to the FastAPI `Response` object injected into the handler.
15. The route handler returns `TokenResponse(access_token=result.access_token, token_type="bearer")`. `ResponseFormatterMiddleware` wraps it in the standard `{success, data, meta}` envelope. The cookie travels alongside in the HTTP response headers.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                                                  |
| ------------ | ------------ | ---------------------------------------------------------------------- |
| `UserEntity` | Read / Write | Looked up by email; `record_login()` stamps `last_login_at` on success |

### Repository Methods Required

| Interface         | Method                 | New?          |
| ----------------- | ---------------------- | ------------- |
| `IUserRepository` | `find_by_email(email)` | No (existing) |
| `IUserRepository` | `save(user)`           | No (existing) |

### New DTOs

_None — `LoginCommand` and `TokenDTO` already exist in `app/application/dtos/auth_dto.py`._

### New Application Interfaces

| Interface              | File                                                  | Notes                                                                                  |
| ---------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `IAuthProvider`        | `app/application/interfaces/auth_provider.py`         | Renames `IAuthStrategy`; method: `authenticate(payload: dict[str, str]) -> AuthResult` |
| `IAuthProviderFactory` | `app/application/interfaces/auth_provider_factory.py` | New abstract creator; method: `create_provider() -> IAuthProvider`                     |

### New Domain Exceptions

| Exception Class      | File                            | Inherits          |
| -------------------- | ------------------------------- | ----------------- |
| `UserSuspendedError` | `app/domain/exceptions/auth.py` | `DomainException` |

### New Error Codes

| Constant            | Value                 | Description                    |
| ------------------- | --------------------- | ------------------------------ |
| `USER_NOT_VERIFIED` | `"USER_NOT_VERIFIED"` | Account email not yet verified |
| `USER_SUSPENDED`    | `"USER_SUSPENDED"`    | Account is suspended           |

### New Utility Functions

Added to `app/core/util.py` (importable from any layer):

| Function                                   | Purpose                                                                                                                                         |
| ------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `set_auth_cookie(response, token) -> None` | Attaches `HttpOnly` `access_token` cookie; reads `ACCESS_TOKEN_EXPIRE_MINUTES` and `ENVIRONMENT` from config to set `Max-Age` and `Secure` flag |
| `clear_auth_cookie(response) -> None`      | Deletes the `access_token` cookie (used by logout, endpoint 1.6)                                                                                |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/credential_login/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.access_token` is a non-empty string
- [x] `res.body.data.token_type` equals `"bearer"`
- [x] `res.body.meta.requestId` is a string
- [x] Response `Set-Cookie` header contains `access_token=Bearer ...`
- [x] Cookie flags include `HttpOnly` and `Path=/`

**Error Cases:**

- [x] `02_invalid_credentials_wrong_password.bru` — Status 401 when password is incorrect → error code `INVALID_CREDENTIALS`
- [x] `03_invalid_credentials_no_account.bru` — Status 401 when email does not exist → error code `INVALID_CREDENTIALS`
- [x] `04_user_not_verified.bru` — Status 403 when account is `PENDING` → error code `USER_NOT_VERIFIED`
- [x] `05_user_suspended.bru` — Status 403 when account is `SUSPENDED` → error code `USER_SUSPENDED`
- [x] `06_validation_error.bru` — Status 422 when email is malformed → `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_credential_login.py`

**Happy Path:**

- [x] `LoginUseCase.execute(LoginCommand(email, password))` returns `TokenDTO` with a non-empty `access_token`
- [x] `UserEntity.record_login()` was called; `last_login_at` is set
- [x] `db_session.commit()` was called exactly once

**Error Cases:**

- [x] Raises `InvalidCredentialsError` when `user_repo.find_by_email()` returns `None`
- [x] Raises `InvalidCredentialsError` when `user.have_password` is `False`
- [x] Raises `InvalidCredentialsError` when `hasher.verify()` returns `False`
- [x] Raises `UserNotVerifiedError` when `user.status == UserStatus.PENDING`
- [x] Raises `UserSuspendedError` when `user.status == UserStatus.SUSPENDED`

**Edge Cases:**

- [x] `CredentialAuthProviderFactory.create_provider()` returns a new `CredentialAuthProvider` instance on each call
- [x] `LoginUseCase` only receives `IAuthProviderFactory` — test that injecting any `IAuthProviderFactory` implementation works (factory substitutability)

---

## Implementation Checklist

- [x] 1. Domain exceptions — add `UserSuspendedError` to `app/domain/exceptions/auth.py`; export from `app/domain/exceptions/__init__.py`
- [x] 2. Error codes — add `USER_NOT_VERIFIED` and `USER_SUSPENDED` to `app/application/errors/error_codes.py`
- [x] 3. Application interfaces — rename `IAuthStrategy` → `IAuthProvider` in `app/application/interfaces/auth_provider.py`; create `IAuthProviderFactory` in `app/application/interfaces/auth_provider_factory.py`; update `app/application/interfaces/__init__.py` exports
- [x] 4. Rename `CredentialProvider` → `CredentialAuthProvider` in `app/infrastructure/auth/credential_provider.py`; implement `IAuthProvider`; add `UserSuspendedError` guard (step 9 in procedures) before `record_login()`
- [x] 5. Create `CredentialAuthProviderFactory` in `app/infrastructure/auth/credential_provider_factory.py`; `create_provider()` returns `CredentialAuthProvider(user_repo=self._user_repo, hasher=self._hasher)`
- [x] 6. Rename `GoogleProvider` → `GoogleAuthProvider` in `app/infrastructure/auth/google_provider.py`; implement `IAuthProvider`; create `GoogleAuthProviderFactory` in `app/infrastructure/auth/google_provider_factory.py` (for 1.5 parity)
- [x] 7. Update `app/infrastructure/auth/__init__.py` exports for all renamed and new classes
- [x] 8. Update `LoginUseCase` in `app/application/use_cases/auth/login.py` — replace `strategy: IAuthStrategy` with `factory: IAuthProviderFactory`; change `execute()` signature to accept `LoginCommand`; call `factory.create_provider()` then `provider.authenticate({"email": command.email, "password": command.password})`
- [x] 9. Exception mapping — add `UserNotVerifiedError` (HTTP 403, `USER_NOT_VERIFIED`) and `UserSuspendedError` (HTTP 403, `USER_SUSPENDED`) to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`
- [x] 10. Cookie utilities — add `set_auth_cookie(response: Response, token: str) -> None` and `clear_auth_cookie(response: Response) -> None` to `app/core/util.py`
- [x] 11. Update `deps.py` — remove `get_credential_strategy`/`get_google_strategy`/`CredentialStrategy`/`GoogleStrategy`; add `get_credential_factory(user_repo, hasher) -> IAuthProviderFactory` and `get_google_factory(user_repo, account_repo) -> IAuthProviderFactory`; add `CredentialAuthFactory`/`GoogleAuthFactory` typed aliases
- [x] 12. Update route handler `app/presentation/api/app_api/v1/auth_routes.py`:
  - Rename function `login` → `credential_login`; set `operation_id="credentialLogin"`
  - Inject FastAPI `Response` into the handler signature
  - Inject `CredentialAuthFactory` instead of `CredentialStrategy`
  - Pass `LoginCommand(email=body.email, password=body.password)` to `execute()`
  - Call `set_auth_cookie(response, result.access_token)` before returning
  - Update Google login route to inject `GoogleAuthFactory`
- [x] 13. Bruno test files (`bruno/auth/credential_login/` — `folder.bru` + `01_success.bru` + 5 error case files)
- [x] 14. Pytest unit tests (`backend/tests/unit/test_credential_login.py`)
