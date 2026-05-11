# Book Catalog — Soft Delete Book Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 4. Book Catalog     |
| Use Case     | 5. Soft Delete Book |
| File Index   | 04_05               |
| Access Level | 🔑 Admin            |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | DELETE                        |
| URL    | `/api/app/v1/books/{book_id}` |
| Auth   | Bearer token (ADMIN role)     |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description              |
| --------- | ------------- | ------------------------ |
| book_id   | string (UUID) | ID of the book to delete |

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
    "id": "01932abc-...",
    "title": "The Great Gatsby",
    "price": "12.99",
    "language": "English",
    "stock_quantity": 10,
    "cover_url": null,
    "isbn": "9780743273565",
    "description": null,
    "page_count": 180,
    "published_date": "1925-04-10",
    "is_active": false,
    "publisher": { "id": "...", "name": "Scribner" },
    "category": null,
    "authors": [],
    "created_at": "2026-01-15T09:00:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-11T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                               |
| ----------- | -------------------- | ------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No or invalid Bearer token                              |
| 401         | TOKEN_EXPIRED        | Bearer token has expired                                |
| 403         | PERMISSION_DENIED    | Authenticated user does not have ADMIN role             |
| 404         | BOOK_NOT_FOUND       | No non-deleted book with the given ID                   |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (malformed UUID path param) |

---

## Procedures

1. **Auth guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token, checks the blocklist via `RedisCacheService`, fetches the user, and asserts `role == UserRole.ADMIN`. Returns HTTP 401/403 on failure; the use case never runs.

2. **Existence check** — Call `await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter("all"))`. `BookStatusFilter("all")` ensures that deactivated books are still found. If the result is `None`, raise `BookNotFoundError(cmd.book_id)`.

3. **Already-deleted guard** — If `book.is_deleted` is `True` (`_deleted_at is not None`), raise `BookNotFoundError(cmd.book_id)`. (The repository already filters deleted records by default, so this branch will only be reached if `find_by_id` with `"all"` is later widened to return deleted records — the check keeps the use case correct regardless.)

4. **Mutation** — Call `book.soft_delete()`. This sets `_deleted_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)` on the entity.

5. **Persist** — Call `await self._book_repo.save(book)`. The repository calls `session.merge(model)` and does **not** commit.

6. **Commit** — Call `await self._db_session.commit()`.

7. **Return** — Build and return `SoftDeleteBookResult` using `self._to_result(book, SoftDeleteBookResult)`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                              |
| ------------ | ------ | ---------------------------------- |
| `BookEntity` | Write  | `soft_delete()` sets `_deleted_at` |

### Repository Methods Required

| Interface         | Method                                           | New?          |
| ----------------- | ------------------------------------------------ | ------------- |
| `IBookRepository` | `find_by_id(book_id, filters: BookStatusFilter)` | No (existing) |
| `IBookRepository` | `save(book: BookEntity)`                         | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                                 |
| ----------------------- | --------------- | -------------------------------------- |
| `SoftDeleteBookCommand` | Command (input) | `book_id: str`                         |
| `SoftDeleteBookResult`  | Result (output) | Inherits `BaseBookResult` (all fields) |

### New Domain Exceptions

_(None — `BookNotFoundError` already exists)_

### New Error Codes

_(None — `BOOK_NOT_FOUND` already exists)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book-catalog/soft-delete-book/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` matches the deleted book ID
- [x] `res.body.data.is_active` is `false`
- [x] `res.body.meta.requestId` is a string
- [x] Subsequent `GET /books/{book_id}` returns 404

**Error Cases:**

- [x] `02_forbidden_user_role.bru` — Status 403 when authenticated as a USER role → error code `PERMISSION_DENIED`
- [x] `03_not_found.bru` — Status 404 when `book_id` does not exist → error code `BOOK_NOT_FOUND`
- [x] `04_already_deleted.bru` — Status 404 when book was previously soft-deleted → error code `BOOK_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_soft_delete_book.py`

**Happy Path:**

- [x] `SoftDeleteBookUseCase.execute(SoftDeleteBookCommand(book_id=...))` returns `SoftDeleteBookResult` with `is_active == False` and `deleted_at` set

**Error Cases:**

- [x] Raises `BookNotFoundError` when no book exists for the given ID
- [x] Raises `BookNotFoundError` when the book is already soft-deleted

**Edge Cases:**

- [x] Soft-deleting a deactivated book (where `deactivated_at` is set) also sets `deleted_at`
- [x] `book.is_active` is `False` on the returned result regardless of prior `deactivated_at` state

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/book_entity.py`) — existing; `soft_delete()` method already present
- [x] 2. Domain exceptions (`app/domain/exceptions/book.py`) — none new
- [x] 3. Repository interface methods (`app/domain/repositories/book_repository.py`) — none new
- [x] 4. DTOs (`app/application/dtos/book_dto.py`) — add `SoftDeleteBookCommand` and `SoftDeleteBookResult`
- [x] 5. Use case (`app/application/use_cases/book/soft_delete_book.py`) — new file
- [x] 6. ORM model — no schema change; `deleted_at` already on `BookModel` via `SoftDeleteMixin`
- [x] 7. Mapper — no change
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/book_repository_impl.py`) — no new methods
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — none new
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — none new
- [x] 11. Pydantic schemas (`app/presentation/schemas/book_schema.py`) — add `SoftDeleteBookResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/book_routes.py`) — add `DELETE /books/{book_id}`
- [x] 13. Wire in `deps.py` — no new providers needed (existing `BookRepo` + `AdminUser`)
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/book-catalog/soft-delete-book/` — `folder.bru` + 6 `.bru` files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_soft_delete_book.py`)
