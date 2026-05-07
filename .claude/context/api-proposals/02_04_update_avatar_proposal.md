# User Profile — Update Avatar Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 2. User Profile  |
| Use Case     | 4. Update Avatar |
| File Index   | 02_04            |
| Access Level | 👤🔑 Both        |
| Status       | Implemented      |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | POST                          |
| URL    | `/api/app/v1/users/me/avatar` |
| Auth   | Bearer token (any role)       |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | multipart/form-data   |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

### Request Body

Multipart form data — single `file` field:

| Field  | Type        | Required | Constraints                                                                                       |
| ------ | ----------- | -------- | ------------------------------------------------------------------------------------------------- |
| `file` | file upload | Yes      | MIME type must be one of `image/jpeg`, `image/png`, `image/gif`, `image/webp`; max size: **5 MB** |

**Example:**

```http
POST /api/app/v1/users/me/avatar
Content-Type: multipart/form-data; boundary=----FormBoundary
Authorization: Bearer eyJ...

------FormBoundary
Content-Disposition: form-data; name="file"; filename="avatar.jpg"
Content-Type: image/jpeg

<binary image data>
------FormBoundary--
```

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "01932abc-...",
    "email": "jane@example.com",
    "full_name": "Jane Doe",
    "date_of_birth": "1990-06-15",
    "role": "user",
    "status": "active",
    "avatar_url": "http://minio:9000/bukoo/avatars/01932abc-...",
    "have_password": true,
    "last_login_at": "2026-05-06T08:00:00Z",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-05-06T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-06T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                   |
| ----------- | ----------------------- | ------------------------------------------- |
| 401         | `UNAUTHORIZED`          | No Authorization header provided            |
| 401         | `TOKEN_EXPIRED`         | Bearer token has expired                    |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or invalid        |
| 404         | `USER_NOT_FOUND`        | Authenticated user no longer exists in DB   |
| 422         | `VALIDATION_ERROR`      | File MIME type is not an allowed image type |
| 422         | `VALIDATION_ERROR`      | File exceeds the 5 MB size limit            |
| 500         | `STORAGE_UPLOAD_FAILED` | MinIO/S3 upload failure                     |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer JWT, checks the revocation blocklist via `RedisCacheService`, and loads the active `UserEntity`. Any token failure raises HTTP 401 before the handler proceeds.

2. **File type validation** — The route handler reads `UploadFile.content_type`. If it is not in `{"image/jpeg", "image/png", "image/gif", "image/webp"}`, raise `HTTPException(status_code=422, detail="Invalid file type. Allowed: image/jpeg, image/png, image/gif, image/webp.")` — identical treatment to a Pydantic input validation failure.

3. **File size validation** — Call `file_data = await file.read()`. If `len(file_data) > 5 * 1024 * 1024` (5 MB), raise `HTTPException(status_code=422, detail="File too large. Maximum size is 5 MB.")`.

4. **Route handler** instantiates `UpdateAvatarUseCase(db_session=db_session, user_repo=user_repo, storage_service=storage_service)` and calls `execute(UpdateAvatarCommand(user_id=current_user.id, file_data=file_data, content_type=file.content_type))`.

5. **User lookup** — Use case calls `user = await self._user_repo.find_by_id(command.user_id)`. If `None` (user deleted between auth guard and use case), raise `UserNotFoundError(command.user_id)`.

6. **Storage upload** — Construct the stable object key: `key = f"avatars/{user.id}"`. Call `await self._storage_service.upload(key, command.file_data, command.content_type)`. MinIO/S3 silently overwrites any prior avatar under the same key, so no explicit delete of the old object is required. If the upload fails, `StorageUploadError` propagates to `domain_exception_handler` and returns HTTP 500 `STORAGE_UPLOAD_FAILED` (after `StorageUploadError` is added to `EXCEPTION_MAP` — see checklist item 9).

7. **Domain mutation** — Call `user.update_avatar(avatar_url=key)`. The entity sets `_avatar_url = key` (the raw object key, not a URL) and `_updated_at = datetime.now(UTC)`.

8. **Persist** — Call `await self._user_repo.save(user)`. Repository merges the ORM model via `session.merge()` but does NOT commit.

9. **Commit** — Call `await self._db_session.commit()`.

10. **Return** — Build and return `UpdateAvatarResult` from the mutated `user` entity fields. The route handler converts `result.avatar_url` (raw object key) to a full public URL via `build_public_url(result.avatar_url)` before placing it in `UserProfileResponse`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                                                                    |
| ------------ | ------ | ---------------------------------------------------------------------------------------- |
| `UserEntity` | Write  | `update_avatar(avatar_url)` sets `_avatar_url` to the object key and bumps `_updated_at` |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `IUserRepository` | `find_by_id(user_id)` | No (existing) |
| `IUserRepository` | `save(user)`          | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                                                                    |
| --------------------- | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `UpdateAvatarCommand` | Command (input) | `user_id: str`, `file_data: bytes`, `content_type: str`                                                                                   |
| `UpdateAvatarResult`  | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — file type/size validation is input validation performed in the route handler; `StorageUploadError` in `app/domain/exceptions/storage.py` already covers storage failures.)_

### New Error Codes

_(None — `STORAGE_UPLOAD_FAILED` and `VALIDATION_ERROR` already exist in `ErrorCode`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/update_avatar/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.avatar_url` is a non-null string containing the user's ID in the path
- [ ] `res.body.data.updated_at` is later than the previous `updated_at`
- [ ] `res.body.meta.requestId` is a non-empty string

**Error Cases (one file each):**

- [ ] `02_no_auth.bru` — Status 401 when no `Authorization` header is provided
- [ ] `03_invalid_token.bru` — Status 401 when token is expired or malformed
- [ ] `04_invalid_file_type.bru` — Status 422 when a non-image file (e.g. `text/plain`) is uploaded → error code `VALIDATION_ERROR`
- [ ] `05_file_too_large.bru` — Status 422 when the uploaded file exceeds 5 MB → error code `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_avatar.py`

**Happy Path:**

- [x] `UpdateAvatarUseCase.execute(valid_command)` returns `UpdateAvatarResult` with `avatar_url` equal to `f"pub/avatars/{user.id}"`
- [x] Returned `updated_at` is later than the entity's original `updated_at`
- [x] Fake storage service's `upload` receives `key="pub/avatars/{user.id}"`, `content_type="image/jpeg"`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`
- [x] Raises `StorageUploadError` when the storage service's `upload` raises `StorageUploadError`

**Edge Cases:**

- [x] Uploading a second avatar results in the same key (`pub/avatars/{user.id}`) — idempotent key strategy confirmed by checking `avatar_url` in the result

---

## Implementation Checklist

- [x] 1. Domain entity — no changes needed (`UserEntity.update_avatar()` already implemented in `app/domain/entities/user_entity.py:133`)
- [x] 2. Domain exceptions — no new exceptions; existing `StorageUploadError` in `app/domain/exceptions/storage.py` is sufficient
- [x] 3. Repository interface — no new methods needed
- [x] 4. Add `UpdateAvatarCommand` and `UpdateAvatarResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case: `app/application/use_cases/user/update_avatar.py`
- [x] 6. ORM model — no new model (existing `UserModel`)
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no new methods
- [x] 9. Exception mapping — add `StorageUploadError → HTTP 500 STORAGE_UPLOAD_FAILED` to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py` (existing gap; needed by this and any future storage endpoint)
- [x] 10. Error codes — no changes needed
- [x] 11. Pydantic schemas — no new schemas; reuse `UserProfileResponse`; FastAPI handles `UploadFile` natively for multipart — no `BaseModel` needed
- [x] 12. Route handler — add `POST /me/avatar` handler to `app/presentation/api/app_api/v1/user_routes.py`
- [x] 13. Wire in `deps.py` — `StorageService` typed alias already exists at `deps.py:114`; no changes needed
- [x] 14. Alembic migration — not required (no schema changes)
- [x] 15. Bruno test files: `bruno/user_profile/update_avatar/folder.bru` + `01_success.bru` through `05_file_too_large.bru`
- [x] 16. Pytest unit tests: `backend/tests/unit/test_update_avatar.py`
