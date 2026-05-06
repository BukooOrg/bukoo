# Auth API Set — Logout Proposal

## Overview

| Field        | Value                         |
| ------------ | ----------------------------- |
| API Set      | 1. Auth                       |
| Use Case     | 6. Logout                     |
| File Index   | 01_06                         |
| Access Level | 👤🔑 Both authenticated roles |
| Status       | Implemented                   |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/auth/logout` |
| Auth   | Bearer token (any role)   |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

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
    "message": "Logged out successfully."
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code    | Condition                                             |
| ----------- | ------------- | ----------------------------------------------------- |
| 401         | INVALID_TOKEN | Authorization header is missing or token is malformed |
| 401         | TOKEN_EXPIRED | Token has already expired                             |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency validates the Bearer token by calling
   `JWTService.decode_token(credentials.credentials)` (raises HTTP 401 on
   `TokenExpiredError` or `InvalidTokenError`). After a successful decode, it
   extracts `jti = str(payload.get("jti", ""))` and calls
   `await token_svc.is_token_revoked(jti)`. If `True`, raises HTTP 401 — the token
   was already revoked by a prior logout. This guard update is a prerequisite for
   the feature to behave correctly on repeated logout attempts.

2. **Capture raw token** — The route handler also declares the `RawToken` typed
   alias — a new dependency in `deps.py` that wraps the shared `_bearer` instance
   and returns `credentials.credentials` as a plain `str`. Because FastAPI caches
   `_bearer`'s result within a single request, the JWT is not decoded twice.

3. **Execute logout use case** — The route handler instantiates `LogoutUseCase`
   with `db_session` and `token_svc`, then calls
   `await use_case.execute(LogoutCommand(access_token=raw_token))`.

4. **Revoke the token** — Inside `LogoutUseCase.execute`, it calls
   `await self._token_svc.revoke_token(command.access_token)`. Inside
   `JWTService.revoke_token`:
   - Decode the raw token via the private jose `jwt.decode` call (bypassing the
     public `decode_token` wrapper to avoid double exception wrapping) to extract
     the `jti` claim (UUID4, embedded at creation time) and the `exp` claim.
   - Compute TTL = `int(exp) − int(datetime.now(UTC).timestamp())`.
   - If TTL > 0, call `await self._cache_svc.set("blocklist:{jti}", "1", ttl_seconds=TTL)`.
   - If TTL ≤ 0, the token is already expired — skip the cache write silently.

5. **No DB commit** — No database mutation occurs.
   `await self._db_session.commit()` is not called.

6. **Clear auth cookie** — The route handler calls `clear_auth_cookie(response)`
   from `app.core.util` to delete the `access_token` HTTP-only cookie.

7. **Return** — Route handler returns `LogoutResponse(message="Logged out successfully.")`.

**`jti` claim prerequisite:** `JWTService.create_access_token` must be updated to
embed a `jti: str(uuid4())` claim in the JWT payload alongside `sub`, `exp`, and
`type`. Tokens issued before this change will not carry a `jti`; `is_token_revoked`
must handle `jti == ""` by returning `False` (legacy tokens are not checked).

---

## Redis Cache Infrastructure

This endpoint introduces `ICacheService` as a new application-layer abstraction
backed by `RedisCacheService`. All future features that need short-lived key-value
storage (rate limiting, OTP storage, feature flags, etc.) will reuse this interface.

### `ICacheService` — Application Interface

**File:** `app/application/interfaces/cache_service.py`

```python
class ICacheService(ABC):
    @abstractmethod
    async def set(self, key: str, value: str, ttl_seconds: int | None = None) -> None: ...

    @abstractmethod
    async def get(self, key: str) -> str | None: ...

    @abstractmethod
    async def delete(self, key: str) -> None: ...

    @abstractmethod
    async def exists(self, key: str) -> bool: ...
```

Export from `app/application/interfaces/__init__.py`.

### `RedisCacheService` — Infrastructure Implementation

**File:** `app/infrastructure/cache/redis_cache.py`
**New package:** `app/infrastructure/cache/__init__.py`

Design decisions for production-readiness:

| Decision           | Choice                                                | Rationale                                                                                    |
| ------------------ | ----------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Client type        | `redis.asyncio.Redis`                                 | Non-blocking; compatible with FastAPI's async event loop                                     |
| Connection pooling | `ConnectionPool.from_url(max_connections=20)`         | Avoids per-request TCP handshakes; 20 covers typical concurrent load                         |
| Key namespacing    | `bukoo:{key}` prefix                                  | Prevents collision if Redis is shared with other processes                                   |
| Response decoding  | `decode_responses=True`                               | Returns `str` instead of `bytes`; avoids manual decoding at every call-site                  |
| Error handling     | Catch `redis.RedisError`, log and re-raise            | Lets callers know cache is unavailable; fail-hard on blocklist writes (security-critical)    |
| Separate Redis DB  | DB 1 (`CACHE_REDIS_URL`) vs DB 0 (Celery `REDIS_URL`) | Independent flush/eviction; Celery queue is not accidentally wiped by `FLUSHDB` on the cache |

**Constructor:** `__init__` creates a `ConnectionPool` from `get_configs().CACHE_REDIS_URL`
and builds a single `Redis` client that reuses it across all method calls. The
connection is lazy — no I/O in `__init__`.

### New Config Field

Add to `RedisConfig` in `app/core/config.py`:

```python
CACHE_REDIS_URL: str = Field(
    description="Redis URL for the application cache (token blocklist, OTP storage, etc.)",
    default="redis://localhost:6379/1",
)
```

DB 1 keeps cache data isolated from Celery's broker queue on DB 0.

### New Dependency in `pyproject.toml`

`celery[redis]` already provides `redis` transitively, but it must be declared as
an explicit direct dependency to prevent silent breakage if the Celery extra is
ever changed:

```
"redis[hiredis]>=4.5.2",
```

`hiredis` is a C-extension parser for the Redis protocol — significantly faster
than the pure-Python parser under concurrent load.

### Wiring in `deps.py`

```python
def get_cache_service() -> ICacheService:
    return RedisCacheService()

CacheService = Annotated[ICacheService, Depends(get_cache_service)]

def get_token_service(cache_svc: CacheService) -> ITokenService:
    return JWTService(cache_svc=cache_svc)

TokenService = Annotated[ITokenService, Depends(get_token_service)]
```

The existing `get_token_service` currently has no arguments; this change adds the
`cache_svc` dependency and threads it into `JWTService.__init__`.

### Docker: RedisInsight Container

Add to `docker/docker-compose.yml` (after the `redis` service):

```yaml
redisinsight:
  image: redis/redisinsight:latest
  container_name: bukoo_redisinsight
  restart: unless-stopped
  depends_on:
    redis:
      condition: service_healthy
  ports:
    - "5540:5540"
  volumes:
    - redisinsight_data:/data
```

Add to the `volumes:` block: `redisinsight_data:`

RedisInsight runs at `http://localhost:5540`. No auth is required in development.

### New Environment Variables

**`docker/.env.dev`** — add under the Redis / Celery section:

```ini
CACHE_REDIS_URL=redis://redis:6379/1
```

**`backend/.env`** — add under the Redis / Celery section:

```ini
CACHE_REDIS_URL=redis://localhost:6379/1
```

Note the host difference: `redis` (Docker service name) in `.env.dev` vs
`localhost` in `backend/.env` (direct local dev without Docker networking).

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                        |
| ------------ | ------ | -------------------------------------------- |
| `UserEntity` | Read   | Resolved by `CurrentUser` guard; not mutated |

### Repository Methods Required

_(None)_

### New DTOs

| DTO Class       | Type            | Fields              |
| --------------- | --------------- | ------------------- |
| `LogoutCommand` | Command (input) | `access_token: str` |
| `LogoutResult`  | Result (output) | `message: str`      |

### New Domain Exceptions

_(None)_

### New Error Codes

_(None — existing `INVALID_TOKEN` and `TOKEN_EXPIRED` cover all error paths)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/auth/logout/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.message` equals `"Logged out successfully."`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_no_auth_header.bru` — Status 401 when Authorization header is absent
- [x] `03_invalid_token.bru` — Status 401 when token is malformed → `INVALID_TOKEN`
- [x] `04_already_logged_out.bru` — Status 401 when the same token is reused after
      logout (blocklist hit in guard) → `INVALID_TOKEN`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_logout.py`

**Happy Path:**

- [x] `LogoutUseCase.execute(LogoutCommand(access_token=valid_token))` calls
      `token_svc.revoke_token` exactly once with the correct token

**Edge Cases:**

- [x] `revoke_token` is called with an already-expired token — no exception raised,
      cache write is skipped (TTL ≤ 0 branch)
- [x] `revoke_token` is called with a token that has no `jti` claim — no exception
      raised, cache write is skipped gracefully

---

## Implementation Checklist

### Redis Cache Infrastructure (prerequisite)

- [x] A. Add `redis[hiredis]>=4.5.2` to `dependencies` in `backend/pyproject.toml`
- [x] B. Add `CACHE_REDIS_URL` field to `RedisConfig` in `app/core/config.py`
- [x] C. Add `CACHE_REDIS_URL=redis://localhost:6379/1` to `backend/.env`
- [x] D. Add `CACHE_REDIS_URL=redis://redis:6379/1` to `docker/.env.dev`
- [x] E. Create `app/application/interfaces/cache_service.py` (`ICacheService` ABC)
- [x] F. Export `ICacheService` from `app/application/interfaces/__init__.py`
- [x] G. Create `app/infrastructure/cache/__init__.py` and
      `app/infrastructure/cache/redis_cache.py` (`RedisCacheService`)
- [x] H. Add `redisinsight` service and `redisinsight_data` volume to
      `docker/docker-compose.yml`

### Logout Feature

- [x] 1. No new domain entity
- [x] 2. No new domain exceptions
- [x] 3. No new repository interface methods
- [x] 4. New DTOs: `LogoutCommand`, `LogoutResult` in `app/application/dtos/auth_dto.py`;
     update `ITokenService` in `app/application/interfaces/token_service.py` — add
     `async revoke_token(token: str) -> None` and
     `async is_token_revoked(jti: str) -> bool` as abstract methods
- [x] 5. New use case: `app/application/use_cases/auth/logout.py` (`LogoutUseCase`)
- [x] 6. No new ORM model
- [x] 7. No new mapper
- [x] 8. Update `JWTService` in `app/infrastructure/auth/jwt_service.py`:
     — constructor gains `cache_svc: ICacheService`;
     — `create_access_token` embeds `jti: str(uuid4())` in the JWT payload;
     — implement `async revoke_token` — decodes token, computes TTL,
     calls `await self._cache_svc.set("blocklist:{jti}", "1", ttl_seconds=ttl)`;
     — implement `async is_token_revoked` — calls
     `await self._cache_svc.exists("blocklist:{jti}")`
- [x] 9. No new exception mapping
- [x] 10. No new error codes
- [x] 11. New Pydantic schema: `LogoutResponse` in `app/presentation/schemas/auth_schema.py`
- [x] 12. New route handler: `POST /logout` in
      `app/presentation/api/app_api/v1/auth_routes.py`
- [x] 13. Update `deps.py`:
      — add `CacheService` provider alias (wraps `RedisCacheService`);
      — update `get_token_service` to accept `cache_svc: CacheService` and
      pass it to `JWTService(cache_svc=cache_svc)`;
      — add `RawToken = Annotated[str, Depends(get_raw_token)]` provider;
      — update `get_current_user` to call `await token_svc.is_token_revoked(jti)`
      after successful decode
- [x] 14. No Alembic migration needed
- [x] 15. Bruno test files: `bruno/auth/logout/` — `folder.bru` + `01_success.bru` + `02_no_auth_header.bru` + `03_invalid_token.bru` +
      `04_already_logged_out.bru`
- [x] 16. Pytest unit tests: `backend/tests/unit/test_logout.py`
