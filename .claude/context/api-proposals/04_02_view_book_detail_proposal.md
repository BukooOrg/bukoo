# Book Catalog — View Book Detail Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 4. Book Catalog     |
| Use Case     | 2. View Book Detail |
| File Index   | 04_02               |
| Access Level | 🌐 Public           |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | GET                           |
| URL    | `/api/app/v1/books/{book_id}` |
| Auth   | None                          |

---

## Request

### Headers

| Header        | Required | Description      |
| ------------- | -------- | ---------------- |
| Content-Type  | No       | application/json |
| Authorization | No       | —                |

### Path Parameters

| Parameter | Type          | Description          |
| --------- | ------------- | -------------------- |
| `book_id` | string (UUID) | The book's UUIDv7 ID |

### Query Parameters

| Parameter | Type   | Required | Default    | Description                                                          |
| --------- | ------ | -------- | ---------- | -------------------------------------------------------------------- |
| `status`  | string | No       | `activate` | Filter by activation state. Allowed: `activate`, `deactivate`, `all` |

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
    "id": "019500ab-...",
    "title": "The Name of the Wind",
    "price": "19.99",
    "language": "English",
    "stock_quantity": 50,
    "cover_url": "https://storage.bukoo.com/books/cover.jpg",
    "isbn": "9780756404741",
    "description": "A detailed fantasy novel...",
    "page_count": 662,
    "published_date": "2007-03-27",
    "is_active": true,
    "publisher": { "id": "019500cd-...", "name": "DAW Books" },
    "category": { "id": "019500ef-...", "name": "Fantasy" },
    "authors": [
      { "id": "019500gh-...", "name": "Patrick Rothfuss", "display_order": 1 }
    ],
    "created_at": "2026-01-10T08:00:00Z",
    "updated_at": "2026-01-10T08:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                                          |
| ----------- | -------------------- | ---------------------------------------------------------------------------------- |
| 404         | BOOK_NOT_FOUND       | No non-deleted book with the given `book_id` matches the requested `status` filter |
| 422         | UNPROCESSABLE_ENTITY | `status` is not one of the three allowed values                                    |

---

## Procedures

1. **Input validation** — FastAPI parses `book_id` from the path as a `str`. The `BookDetailQueryRequest` Pydantic schema validates `status` against `Literal["activate", "deactivate", "all"]` (default `"activate"`). A disallowed value yields HTTP 422 automatically.

2. **Map `status` to `activate_flag`** — `BookDetailQueryRequest.to_command()` converts the public query-param value to the internal repository representation used by `BookFilters`:
   - `"activated_book"` → `activate_flag = "activate"`
   - `"deactivated_book"` → `activate_flag = "deactivate"`
   - `"all"` → `activate_flag = None`
     The mapped value is stored in `ViewBookDetailCommand.activate_flag`.

3. **Repo lookup** — `ViewBookDetailUseCase.execute()` calls `await self._book_repo.find_by_id(cmd.book_id, cmd.activate_flag)`. The updated `find_by_id()` always applies `BookModel.deleted_at.is_(None)` and additionally branches on `activate_flag`:
   - `"activate"` → adds `BookModel.deactivated_at.is_(None)`
   - `"deactivate"` → adds `BookModel.deactivated_at.is_not(None)`
   - `None` → no further filter on `deactivated_at` (any non-deleted book is returned)
     The query eager-loads `publisher`, `category`, and `author_associations → author` via `selectinload` (same as `find_all`).

4. **Not found check** — If `find_by_id()` returns `None`, raise `BookNotFoundError(cmd.book_id)`. The existing `EXCEPTION_MAP` converts this to HTTP 404 with error code `BOOK_NOT_FOUND`.

5. **Return** — Build and return `BookDetailResult` from the `BookEntity`, including all selectin-loaded relationships.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                                            |
| ------------ | ------ | ---------------------------------------------------------------- |
| `BookEntity` | Read   | Includes selectin-loaded `publisher`, `category`, `authors` list |

### Repository Methods Required

| Interface         | Method                                          | New?                                                                                             |
| ----------------- | ----------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| `IBookRepository` | `find_by_id(book_id, activate_flag="activate")` | Modified — add `activate_flag: Literal["activate", "deactivate"] \| None = "activate"` parameter |

### New DTOs

| DTO Class               | Type            | Fields                                                                                      |
| ----------------------- | --------------- | ------------------------------------------------------------------------------------------- |
| `ViewBookDetailCommand` | Command (input) | `book_id: str`, `activate_flag: Literal["activate", "deactivate"] \| None`                  |
| `BookDetailResult`      | Result (output) | All fields of `BaseBookResult` + `deactivated_at: datetime \| None`, `updated_at: datetime` |

### New Domain Exceptions

_(None — `BookNotFoundError` already exists in `app/domain/exceptions/book.py`)_

### New Error Codes

_(None — `BOOK_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book/view_book_detail/`

**`01_success_activated.bru` — Happy Path (activated book):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.is_active` is `true`
- [x] `res.body.data.authors` is an array
- [x] `res.body.meta.requestId` is a string

**Error / edge cases (one file each):**

- [x] `02_success_deactivated.bru` — Status 200 with `?status=deactivated_book`; `res.body.data.is_active` is `false`
- [x] `03_success_all.bru` — Status 200 with `?status=all`; book returned regardless of activation state
- [x] `04_not_found.bru` — Status 404, error code `BOOK_NOT_FOUND` for a random UUID
- [x] `05_deactivated_not_visible_default.bru` — Status 404 when fetching a known-deactivated book without `status` param
- [x] `06_unknown_status.bru` — Status 422 for an unsupported `status` value (e.g. `"unknown"`)

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_book_detail.py`

**Happy Path:**

- [x] `ViewBookDetailUseCase.execute(valid_command)` returns `BookDetailResult` with correct `id`, `title`, `is_active`, `publisher`, `category`, and `authors`

**Error Cases:**

- [x] Raises `BookNotFoundError` when `find_by_id()` returns `None`

**Edge Cases:**

- [x] Returns a deactivated book when `status = "deactivate"`
- [x] Raises `BookNotFoundError` when an activate-only request is made for a deactivated book

---

## Implementation Checklist

- [x] 1. Domain entity — `BookEntity` exists, no changes needed
- [x] 2. Domain exceptions — `BookNotFoundError` exists, no changes needed
- [x] 3. Repository interface — Modify `find_by_id()` signature in `IBookRepository` (`app/domain/repositories/book_repository.py`)
- [x] 4. DTOs — Add `ViewBookDetailCommand` and `BookDetailResult` to `app/application/dtos/book_dto.py`
- [x] 5. Use case — `app/application/use_cases/book/view_book_detail.py`
- [x] 6. ORM model — `BookModel` exists, no changes needed
- [x] 7. Mapper — `BookMapper` exists, no changes needed
- [x] 8. Repository implementation — Update `find_by_id()` in `BookRepositoryImpl` to accept and apply `activate_flag` (`app/infrastructure/db/repositories/book_repository_impl.py`)
- [x] 9. Exception mapping — `BookNotFoundError` already mapped, no changes needed
- [x] 10. Error codes — `BOOK_NOT_FOUND` already exists, no changes needed
- [x] 11. Pydantic schemas — Add `BookDetailQueryRequest` and `BookDetailResponse` to `app/presentation/schemas/book_schema.py`
- [x] 12. Route handler — Add `GET /books/{book_id}` to `app/presentation/api/app_api/v1/book_routes.py`
- [x] 13. Wire in `deps.py` — `BookRepo` already wired, no changes needed
- [x] 14. Alembic migration — Not needed (no schema changes)
- [x] 15. Bruno test files — `bruno/book/view_book_detail/folder.bru` + six test files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_view_book_detail.py`
