# Auth API Set — OAuth Login URL Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 1. Auth API Set     |
| Use Case     | 5a. OAuth Login URL |
| File Index   | 01_05a              |
| Access Level | 🌐 Public           |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                                     |
| ------ | ----------------------------------------- |
| Method | GET                                       |
| URL    | `/api/app/v1/auth/oauth/{provider}/login` |
| Auth   | None                                      |

---

## Request

### Headers

_None required._

### Path Parameters

| Parameter | Type   | Description                                   |
| --------- | ------ | --------------------------------------------- |
| provider  | string | OAuth provider name (currently only `google`) |

### Query Parameters

_None_

### Request Body

_None_

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=openid+email+profile&state=abc123..."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

The frontend receives this URL and executes `window.location.href = url` to redirect the browser to the provider's consent screen.

### Error Responses

| HTTP Status | Error Code               | Condition                                               |
| ----------- | ------------------------ | ------------------------------------------------------- |
| 400         | OAUTH_PROVIDER_NOT_FOUND | `{provider}` is not registered in the provider registry |
| 422         | VALIDATION_ERROR         | Pydantic validation failure                             |

---

## Procedures

1. The route handler looks up `{provider}` in the `OAuthProviderRegistry` dict (injected via `deps.py`). If the key is absent, raise `OAuthProviderNotFoundError` — caught by `EXCEPTION_MAP` → HTTP 400.

2. Retrieve the `IOAuthProviderFactory` for the provider. Pass it to `GetOAuthLoginUrlUseCase`.

3. `GetOAuthLoginUrlUseCase.execute()`:

   a. Generate a cryptographically secure CSRF state token: `state = secrets.token_urlsafe(32)`.

   b. Store the state in Redis via `cache_svc.set(f"oauth_state:{state}", "1", ttl_seconds=600)`. The 10-minute TTL gives the user ample time to complete the consent screen while keeping the attack window short.

   c. Call `self._factory.create_provider()` — **factory method invocation** — which returns a concrete `IOAuthProvider` instance (`GoogleOAuthProvider`). The use case depends only on the `IOAuthProviderFactory` abstraction; it has no knowledge of `GoogleOAuthProvider`.

   d. Call `oauth_provider.get_authorization_url(state=state)`. `GoogleOAuthProvider` constructs the full authorization URL using `urllib.parse.urlencode` with `client_id`, `redirect_uri`, `response_type=code`, `scope=openid email profile`, and the `state` token.

   e. Return `GetOAuthLoginUrlResult(url=url)`.

4. Route handler returns `OAuthLoginUrlResponse(url=result.url)`.

---

## Factory Method Pattern Application

```
IOAuthProviderFactory          ← abstract creator  (application/interfaces/)
      │
      └── GoogleOAuthProviderFactory  ← concrete creator (infrastructure/oauth/)
                │
                └── create_provider() → GoogleOAuthProvider  ← concrete product

IOAuthProvider                 ← abstract product  (application/interfaces/)
      │
      └── GoogleOAuthProvider        ← concrete product (infrastructure/oauth/)
                │
                ├── get_authorization_url(state) → str
                ├── get_access_token(code) → str        [used by 01_05b]
                └── get_user_info(token) → OAuthUserInfo [used by 01_05b]

GetOAuthLoginUrlUseCase        ← consumer; depends only on IOAuthProviderFactory
OAuthCallbackUseCase           ← consumer; depends only on IOAuthProviderFactory [01_05b]
```

The `OAuthProviderRegistry` in `deps.py` is a `dict[str, IOAuthProviderFactory]`. Adding a new provider (e.g., GitHub) requires only: a new `IOAuthProvider` implementation, a new factory, and a new registry entry — no changes to use cases or route handlers.

---

## Domain Impact

### Entities Involved

_None — no database reads or writes in this use case._

### Repository Methods Required

_None_

### New DTOs

| DTO Class                | Type            | Fields                                                          |
| ------------------------ | --------------- | --------------------------------------------------------------- |
| `OAuthUserInfo`          | Shared value    | `id: str`, `email: str`, `name: str`, `avatar_url: str \| None` |
| `GetOAuthLoginUrlResult` | Result (output) | `url: str`                                                      |

(`OAuthUserInfo` is introduced here and shared with `OAuthCallbackUseCase` in 01_05b.)

No command DTO — `GetOAuthLoginUrlUseCase.execute()` takes no arguments; all inputs are injected via `__init__`.

### New Application Interfaces

| Interface               | File                                                   | Key Methods                                                                                                                                           |
| ----------------------- | ------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------- |
| `IOAuthProvider`        | `app/application/interfaces/oauth_provider.py`         | `get_authorization_url(state: str) -> str` (sync), `get_access_token(code: str) -> str` (async), `get_user_info(token: str) -> OAuthUserInfo` (async) |
| `IOAuthProviderFactory` | `app/application/interfaces/oauth_provider_factory.py` | `create_provider() -> IOAuthProvider`                                                                                                                 |

### New Domain Exceptions

| Exception Class              | File                            | Inherits          |
| ---------------------------- | ------------------------------- | ----------------- |
| `OAuthProviderNotFoundError` | `app/domain/exceptions/auth.py` | `DomainException` |

### New Error Codes

| Constant                   | Value                        | Description                   |
| -------------------------- | ---------------------------- | ----------------------------- |
| `OAUTH_PROVIDER_NOT_FOUND` | `"OAUTH_PROVIDER_NOT_FOUND"` | Provider name not in registry |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/oauth_login_url/`

**`01_success_google.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.url` is a string starting with `https://accounts.google.com/o/oauth2/v2/auth`
- [ ] `res.body.data.url` contains `state=` query param
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_invalid_provider.bru` — `GET /auth/oauth/github/login` → Status 400 → error code `OAUTH_PROVIDER_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_oauth_login_url.py`

**Happy Path:**

- [ ] `GetOAuthLoginUrlUseCase.execute()` returns `GetOAuthLoginUrlResult` with a non-empty `url`
- [ ] The returned `url` contains the `state` parameter that was stored in the fake cache

**Error Cases:**

- [ ] Route handler raises `OAuthProviderNotFoundError` when `provider` is absent from the registry

**Edge Cases:**

- [ ] Each call to `execute()` generates a unique `state` value (no collisions across two calls)
- [ ] `cache_svc.set` is called with key `oauth_state:{state}` and `ttl_seconds=600`

---

## Implementation Checklist

- [x] 1. Domain entity — no change
- [x] 2. Domain exceptions — add `OAuthProviderNotFoundError` to `app/domain/exceptions/auth.py`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interfaces — no new methods
- [x] 4. New application interfaces — `IOAuthProvider` (`app/application/interfaces/oauth_provider.py`) and `IOAuthProviderFactory` (`app/application/interfaces/oauth_provider_factory.py`); export both from `app/application/interfaces/__init__.py`
- [x] 5. New DTOs — add `OAuthUserInfo` and `GetOAuthLoginUrlResult` to `app/application/dtos/auth_dto.py`
- [x] 6. Use case — `app/application/use_cases/auth/get_oauth_login_url.py` (`GetOAuthLoginUrlUseCase`)
- [x] 7. ORM model — no change
- [x] 8. Mapper — no change
- [x] 9. Repository implementation — no change
- [x] 10. New infrastructure directory — `app/infrastructure/oauth/__init__.py`, `google_oauth_provider.py` (`GoogleOAuthProvider` implements `IOAuthProvider`), `google_oauth_provider_factory.py` (`GoogleOAuthProviderFactory` implements `IOAuthProviderFactory`)
- [x] 11. Exception mapping — add `OAuthProviderNotFoundError → HTTP 400, OAUTH_PROVIDER_NOT_FOUND` in `app/presentation/http/exception_mapper.py`
- [x] 12. Error codes — add `OAUTH_PROVIDER_NOT_FOUND = "OAUTH_PROVIDER_NOT_FOUND"` in `app/application/errors/error_codes.py`
- [x] 13. Pydantic schemas — add `OAuthLoginUrlResponse(url: str)` to `app/presentation/schemas/auth_schema.py`
- [x] 14. Route handler — add `oauth_login_url()` to `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 15. Wire in `deps.py` — add `get_oauth_provider_registry()` returning `dict[str, IOAuthProviderFactory]` and `OAuthProviderRegistry` typed alias
- [x] 16. Alembic migration — no schema change required
- [x] 17. Bruno test files (`bruno/auth/oauth_login_url/` — `folder.bru` + `01_success_google.bru` + `02_invalid_provider.bru`)
- [x] 18. Pytest unit tests (`backend/tests/unit/test_get_oauth_login_url.py`)

### `deps.py` wiring (reference)

```python
def get_oauth_provider_registry() -> dict[str, IOAuthProviderFactory]:
    configs = get_configs()
    return {
        "google": GoogleOAuthProviderFactory(
            client_id=configs.GOOGLE_CLIENT_ID.get_secret_value(),
            client_secret=configs.GOOGLE_CLIENT_SECRET.get_secret_value(),
            redirect_uri=configs.GOOGLE_REDIRECT_URI,
        ),
    }

OAuthProviderRegistry = Annotated[
    dict[str, IOAuthProviderFactory], Depends(get_oauth_provider_registry)
]
```
