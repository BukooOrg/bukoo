# User Profile — Get Me Proposal

## Overview

| Field        | Value                         |
| ------------ | ----------------------------- |
| API Set      | 2. User Profile               |
| Use Case     | 1. Get Me                     |
| File Index   | 02_01                         |
| Access Level | 👤🔑 Both authenticated roles |
| Status       | Implemented                   |

---

## Endpoint

| Field  | Value                                       |
| ------ | ------------------------------------------- |
| Method | GET                                         |
| URL    | `/api/app/v1/users/me`                      |
| Auth   | Bearer token (any role — `USER` or `ADMIN`) |

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
    "id": "019dfafe-c7c5-7a9e-91da-998f3151eb52",
    "email": "john@example.com",
    "full_name": "John Doe",
    "date_of_birth": "1990-01-15",
    "role": "user",
    "status": "active",
    "avatar_url": "http://localhost:9000/bookstore/pub/avatar/019dfafe-c7c5-7a9e-91da-998f3151eb52",
    "have_password": true,
    "last_login_at": "2026-01-15T10:30:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

`avatar_url` is `null` when no avatar has been uploaded. When present, it is the
fully-qualified public URL constructed from the stored object key (e.g.
`pub/avatar/019dfafe-...` → `http://localhost:9000/bookstore/pub/avatar/019dfafe-...`
in development, or the S3 equivalent in production).

### Error Responses

| HTTP Status | Error Code         | Condition                                            |
| ----------- | ------------------ | ---------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID | No Authorization header, token malformed, or expired |
| 401         | AUTH_TOKEN_INVALID | Token valid but user not found or not active         |

---

## Procedures

This endpoint has no dedicated use case. The `CurrentUser` dependency already
fetches and validates the `UserEntity`; the route handler maps it to the
response schema directly, avoiding a redundant DB query.

1. **[Auth guard]** `CurrentUser` dependency validates the Bearer token via
   `JWTService.decode_token`. If invalid or expired → raises HTTP 401 (handled
   in `deps.py`, not here).
2. **[User guard]** `CurrentUser` calls `user_repo.find_by_id(sub)`. If user
   not found or `user.is_active == False` → raises HTTP 401 (handled in
   `deps.py`).
3. **[URL construction]** Route handler calls `build_public_url(user.avatar_url)`
   to convert the stored object key into a fully-qualified URL.
4. **[Return]** Route handler builds and returns `UserProfileResponse` from
   the resolved `UserEntity`.

---

## Utility Function: `build_public_url`

**Location:** `app/core/util.py`

```python
def build_public_url(key: str | None) -> str | None:
    """Convert a stored object storage key to its public-facing URL.

    Keys under pub/ are publicly readable; the URL is constructed directly
    from config rather than generating a signed URL (which would expire).

    MinIO  → http(s)://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{key}
    S3     → https://{AWS_S3_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{key}
    """
    if key is None:
        return None

    configs = get_configs()
    match configs.STORAGE_TYPE:
        case ObjectStorageType.MINIO:
            protocol = "https" if configs.MINIO_USE_SSL else "http"
            return f"{protocol}://{configs.MINIO_ENDPOINT}/{configs.MINIO_BUCKET}/{key}"
        case ObjectStorageType.S3:
            return (
                f"https://{configs.AWS_S3_BUCKET}"
                f".s3.{configs.AWS_REGION}.amazonaws.com/{key}"
            )
        case _:
            return key
```

This function reads config inside the body (never at module level) and is safe
to call from any layer. It is also reused by future endpoints that expose
avatar or cover image URLs (e.g. `GET /books/{id}`, `GET /users/{id}`).

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                        |
| ------------ | ------ | -------------------------------------------- |
| `UserEntity` | Read   | Already resolved by `CurrentUser` dependency |

### Repository Methods Required

_(None — `find_by_id` is already called inside `CurrentUser`; no additional
repository call is needed)_

### New DTOs

_(None — `UserEntity` is mapped directly to a Pydantic response schema in the
presentation layer)_

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**File:** `bruno/user-profile/get-me.bru`

**Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.data.email` matches the logged-in user's email
- [x] `res.body.data.role` is `"user"` or `"admin"`
- [x] `res.body.data.status` is `"active"`
- [x] `res.body.data.avatar_url` is either `null` or a string starting with `http`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] Status 401 when no Authorization header provided
- [x] Status 401 when token is expired or malformed

### Pytest Unit Tests

_(No use case to unit-test. Integration tests cover the route end-to-end.)_

---

## Implementation Checklist

- [x] 1. `build_public_url` utility → `app/core/util.py`
- [x] 2. `UserProfileResponse` Pydantic schema → `app/presentation/schemas/user_schema.py`
- [x] 3. Route handler `GET /users/me` → `app/presentation/api/app_api/v1/user_routes.py`
- [x] 4. Register `user_router` in `app/presentation/api/app_api/v1/__init__.py`
- [x] 5. Bruno test files → `bruno/user_profile/get_me/`
