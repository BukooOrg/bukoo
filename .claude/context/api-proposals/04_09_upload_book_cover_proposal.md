# Book Catalog — Upload Book Cover Proposal

## Overview

| Field        | Value                |
| ------------ | -------------------- |
| API Set      | 4. Book Catalog      |
| Use Case     | 9. Upload Book Cover |
| File Index   | 04_09                |
| Access Level | 🔑 Admin             |
| Status       | Implemented          |

---

## Endpoint

| Field  | Value                               |
| ------ | ----------------------------------- |
| Method | POST                                |
| URL    | `/api/app/v1/books/{book_id}/cover` |
| Auth   | Bearer token (ADMIN role)           |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | multipart/form-data   |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                              |
| --------- | ------------- | ---------------------------------------- |
| book_id   | string (UUID) | The ID of the book to upload a cover for |

### Query Parameters

_(None)_

### Request Body

| Field | Type   | Required | Constraints                                                                         |
| ----- | ------ | -------- | ----------------------------------------------------------------------------------- |
| file  | binary | Yes      | Multipart file upload; content type in `ALLOWED_COVER_TYPES`; max `MAX_COVER_BYTES` |

_(Multipart form-data — no JSON body)_

---

## Response

### Success Response

**Status:** 200 OK

```json
{
  "success": true,
  "data": {
    "id": "01932abc-...",
    "title": "The Great Gatsby",
    "price": "12.99",
    "language": "en",
    "stock_quantity": 50,
    "cover_url": "https://storage.example.com/pub/covers/01932abc-...",
    "isbn": "9780743273565",
    "description": null,
    "page_count": 180,
    "published_date": "1925-04-10",
    "is_active": true,
    "publisher": { "id": "...", "name": "Scribner" },
    "category": { "id": "...", "name": "Fiction" },
    "authors": [
      { "id": "...", "name": "F. Scott Fitzgerald", "display_order": 1 }
    ],
    "created_at": "2026-01-10T08:00:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-11T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                     |
| ----------- | ----------------------- | ------------------------------------------------------------- |
| 401         | `NOT_AUTH_HEADER`       | No Authorization header provided                              |
| 401         | `TOKEN_EXPIRED`         | Bearer token has expired                                      |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or revoked                          |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have the ADMIN role               |
| 404         | `BOOK_NOT_FOUND`        | No book found for the given `book_id` (or it is soft-deleted) |
| 422         | `INVALID_FILE_TYPE`     | File content type is not in `ALLOWED_COVER_TYPES`             |
| 422         | `FILE_SIZE_EXCEEDED`    | File size exceeds `MAX_COVER_BYTES`                           |
| 500         | `STORAGE_UPLOAD_FAILED` | Upload to MinIO/S3 failed                                     |

---

## Procedures

1. **Auth/guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the Redis blocklist for revocation, and asserts `user.role == UserRole.ADMIN`. Raises HTTP 401 or 403 if any check fails.

2. **File type validation** — In the route handler (not the use case), check `file.content_type not in ALLOWED_COVER_TYPES`. If invalid, raise `InvalidFileTypeError(ALLOWED_COVER_TYPES)`. This maps to HTTP 422 / `INVALID_FILE_TYPE`.

3. **File size validation** — In the route handler, read the full file bytes with `file_data = await file.read()`. If `len(file_data) > MAX_COVER_BYTES`, raise `FileSizeExceededError(MAX_COVER_BYTES // 1024**2, "MB")`. This maps to HTTP 422 / `FILE_SIZE_EXCEEDED`.

4. **Fetch the book** — In the use case, call `await book_repo.find_by_id(command.book_id, BookStatusFilter(status="all"))`. Using `status="all"` allows cover uploads for both active and deactivated books, while still excluding soft-deleted records.

5. **Existence check** — If `find_by_id` returns `None`, raise `BookNotFoundError(command.book_id)`. This maps to HTTP 404 / `BOOK_NOT_FOUND`.

6. **Upload to storage** — Call `await storage_svc.upload(key, command.file_data, command.content_type)` where `key = f"pub/covers/{command.book_id}"`. If the upload fails, `IStorageService` raises `StorageUploadError`, which maps to HTTP 500 / `STORAGE_UPLOAD_FAILED`. Uploading to a fixed, deterministic key means re-uploading a cover silently replaces the previous one.

7. **Mutate the entity** — Call `book.set_cover_url(cover_url=key)`. The new entity method sets `_cover_url = cover_url` and `_updated_at = datetime.now(UTC)`.

8. **Persist** — Call `await book_repo.save(book)`. The repository executes `session.merge(model)` but does NOT commit.

9. **Commit** — Call `await self._db_session.commit()` to flush the unit of work.

10. **Return** — Build and return `UploadBookCoverResult` from the mutated `BookEntity`, mapping all fields from `BaseBookResult`. `cover_url` will hold the storage key; the route handler applies `build_public_url(result.cover_url)` before returning the response.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                                                     |
| ------------ | ------------ | ------------------------------------------------------------------------- |
| `BookEntity` | Read / Write | New `set_cover_url(cover_url)` method sets `_cover_url` and `_updated_at` |

### Repository Methods Required

| Interface         | Method                                  | New?          |
| ----------------- | --------------------------------------- | ------------- |
| `IBookRepository` | `find_by_id(book_id, BookStatusFilter)` | No (existing) |
| `IBookRepository` | `save(book)`                            | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                                                  |
| ------------------------ | --------------- | ------------------------------------------------------- |
| `UploadBookCoverCommand` | Command (input) | `book_id: str`, `file_data: bytes`, `content_type: str` |
| `UploadBookCoverResult`  | Result (output) | Extends `BaseBookResult`                                |

### New Domain Exceptions

_(None — `BookNotFoundError`, `InvalidFileTypeError`, `FileSizeExceededError`, and `StorageUploadError` all exist)_

### New Error Codes

_(None — `BOOK_NOT_FOUND`, `INVALID_FILE_TYPE`, `FILE_SIZE_EXCEEDED`, and `STORAGE_UPLOAD_FAILED` all exist)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book/upload_book_cover/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.cover_url` is a non-null string
- [ ] `res.body.data.id` equals the book ID used in the request
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_forbidden_non_admin.bru` — Status 403 when a USER-role token is used → `ADMIN_ACCESS_REQUIRED`
- [ ] `03_book_not_found.bru` — Status 404 when `book_id` does not exist → `BOOK_NOT_FOUND`
- [ ] `04_invalid_file_type.bru` — Status 422 when file content type is not an allowed image type → `INVALID_FILE_TYPE`
- [ ] `05_file_too_large.bru` — Status 422 when file exceeds `MAX_COVER_BYTES` → `FILE_SIZE_EXCEEDED`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_upload_book_cover.py`

**Happy Path:**

- [ ] `UploadBookCoverUseCase.execute(valid_command)` calls `storage_svc.upload` with key `pub/covers/{book_id}` and returns `UploadBookCoverResult` with a non-null `cover_url`

**Error Cases:**

- [ ] Raises `BookNotFoundError` when `book_repo.find_by_id` returns `None`

**Edge Cases:**

- [ ] Re-uploading a cover for the same book succeeds and overwrites the previous key
- [ ] A soft-deleted book (simulated by the fake repo returning `None`) is treated the same as not-found

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/book_entity.py`) — **add** `set_cover_url(cover_url: str) -> None` method
- [x] 2. Domain exceptions — existing; no new exceptions needed
- [x] 3. Repository interface (`app/domain/repositories/book_repository.py`) — existing; no changes needed
- [x] 4. DTOs (`app/application/dtos/book_dto.py`) — **add** `UploadBookCoverCommand` and `UploadBookCoverResult`
- [x] 5. Use case (`app/application/use_cases/book/upload_book_cover.py`) — **new file**; export from `app/application/use_cases/book/__init__.py`
- [x] 6. ORM model — existing; no migration needed
- [x] 7. Mapper — existing; no changes needed
- [x] 8. Repository implementation — existing; no changes needed
- [x] 9. Exception mapping — existing; no changes needed
- [x] 10. Error codes — existing; no changes needed
- [x] 11. Constants (`app/core/constants.py`) — **add** `ALLOWED_COVER_TYPES` and `MAX_COVER_BYTES`
- [x] 12. Pydantic schemas (`app/presentation/schemas/book_schema.py`) — **add** `UploadBookCoverResponse(BaseBookResponse)`
- [x] 13. Route handler (`app/presentation/api/app_api/v1/book_routes.py`) — **add** `POST /{book_id}/cover`; file type and size validation happens here before calling the use case
- [x] 14. Wire in `deps.py` — existing; `BookRepo`, `AdminUser`, `StorageService`, and `DbSession` already wired, no changes needed
- [x] 15. Alembic migration — **not required** (no schema change)
- [x] 16. Bruno test files (`bruno/book/upload_book_cover/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 17. Pytest unit tests (`backend/tests/unit/test_upload_book_cover.py`)
