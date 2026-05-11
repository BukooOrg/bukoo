# Book Catalog — Deactivate Book Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 4. Book Catalog    |
| Use Case     | 6. Deactivate Book |
| File Index   | 04_06              |
| Access Level | 🔑 Admin           |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                                    |
| ------ | ---------------------------------------- |
| Method | PATCH                                    |
| URL    | `/api/app/v1/books/{book_id}/deactivate` |
| Auth   | Bearer token (ADMIN role)                |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                      |
| --------- | ------------- | -------------------------------- |
| book_id   | string (UUID) | The ID of the book to deactivate |

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
    "language": "en",
    "stock_quantity": 50,
    "cover_url": null,
    "isbn": "9780743273565",
    "description": null,
    "page_count": 180,
    "published_date": "1925-04-10",
    "is_active": false,
    "publisher": { "id": "...", "name": "Scribner" },
    "category": { "id": "...", "name": "Fiction" },
    "authors": [
      { "id": "...", "name": "F. Scott Fitzgerald", "display_order": 1 }
  x],
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

| HTTP Status | Error Code                 | Condition                                                     |
| ----------- | -------------------------- | ------------------------------------------------------------- |
| 401         | `NOT_AUTH_HEADER`          | No Authorization header provided                              |
| 401         | `TOKEN_EXPIRED`            | Bearer token has expired                                      |
| 401         | `INVALID_TOKEN`            | Bearer token is malformed or revoked                          |
| 403         | `ADMIN_ACCESS_REQUIRED`    | Authenticated user does not have the ADMIN role               |
| 404         | `BOOK_NOT_FOUND`           | No book found for the given `book_id` (or it is soft-deleted) |
| 409         | `BOOK_ALREADY_DEACTIVATED` | The book is already deactivated                               |
| 422         | `VALIDATION_ERROR`         | Pydantic validation failure (e.g. malformed path param)       |

---

## Procedures

1. **Auth/guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the Redis blocklist for revocation, and asserts `user.role == UserRole.ADMIN`. Raises HTTP 401 or 403 if any check fails. The use case receives no user argument.

2. **Fetch the book** — Call `await book_repo.find_by_id(command.book_id, BookStatusFilter(status="all"))`. Using `status="all"` finds the book regardless of whether it is currently active or deactivated, while still excluding soft-deleted records (the repo always applies `BookModel.deleted_at.is_(None)`).

3. **Existence check** — If `find_by_id` returns `None`, raise `BookNotFoundError(command.book_id)`. This maps to HTTP 404 / `BOOK_NOT_FOUND`.

4. **Idempotency guard** — If `not book.is_active` (i.e. `book.deactivated_at is not None`), the book is already hidden from the storefront. Raise `BookAlreadyDeactivatedError(command.book_id)`. This maps to HTTP 409 / `BOOK_ALREADY_DEACTIVATED`.

5. **Mutate the entity** — Call `book.deactivate()`. The method sets `_deactivated_at = datetime.now(UTC)` and `_updated_at = datetime.now(UTC)` on the entity.

6. **Persist** — Call `await book_repo.save(book)`. The repository executes `session.merge(model)` but does NOT commit.

7. **Commit** — Call `await self._db_session.commit()` to flush the unit of work.

8. **Return** — Build and return `DeactivateBookResult` from the mutated `BookEntity`, mapping all fields from `BaseBookResult`. `is_active` will be `False`.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                              |
| ------------ | ------------ | -------------------------------------------------- |
| `BookEntity` | Read / Write | Calls `book.deactivate()` to set `_deactivated_at` |

### Repository Methods Required

| Interface         | Method                                  | New?          |
| ----------------- | --------------------------------------- | ------------- |
| `IBookRepository` | `find_by_id(book_id, BookStatusFilter)` | No (existing) |
| `IBookRepository` | `save(book)`                            | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                   |
| ----------------------- | --------------- | ------------------------ |
| `DeactivateBookCommand` | Command (input) | `book_id: str`           |
| `DeactivateBookResult`  | Result (output) | Extends `BaseBookResult` |

### New Domain Exceptions

| Exception Class               | File                            | Inherits          |
| ----------------------------- | ------------------------------- | ----------------- |
| `BookAlreadyDeactivatedError` | `app/domain/exceptions/book.py` | `DomainException` |

### New Error Codes

| Constant                   | Value                        | Description                 |
| -------------------------- | ---------------------------- | --------------------------- |
| `BOOK_ALREADY_DEACTIVATED` | `"BOOK_ALREADY_DEACTIVATED"` | Book is already deactivated |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book/deactivate_book/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.is_active` is `false`
- [x] `res.body.data.id` equals the book ID used in the request
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when a USER-role token is used → `ADMIN_ACCESS_REQUIRED`
- [x] `03_book_not_found.bru` — Status 404 when `book_id` does not exist → `BOOK_NOT_FOUND`
- [x] `04_already_deactivated.bru` — Status 409 when book is already deactivated → `BOOK_ALREADY_DEACTIVATED`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_deactivate_book.py`

**Happy Path:**

- [x] `DeactivateBookUseCase.execute(valid_command)` returns `DeactivateBookResult` with `is_active == False`

**Error Cases:**

- [x] Raises `BookNotFoundError` when `book_repo.find_by_id` returns `None`
- [x] Raises `BookAlreadyDeactivatedError` when the book's `deactivated_at` is already set

**Edge Cases:**

- [x] A soft-deleted book (simulated by the fake repo returning `None`) is treated the same as not-found

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/book_entity.py`) — existing; `deactivate()` method already present, no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/book.py`) — **add** `BookAlreadyDeactivatedError`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/book_repository.py`) — existing; `find_by_id` and `save` already defined, no changes needed
- [x] 4. DTOs (`app/application/dtos/book_dto.py`) — **add** `DeactivateBookCommand` and `DeactivateBookResult`
- [x] 5. Use case (`app/application/use_cases/book/deactivate_book.py`) — **new file**; export from `app/application/use_cases/book/__init__.py`
- [x] 6. ORM model — existing; `BookModel` already has `deactivated_at`, no migration needed
- [x] 7. Mapper — existing; `BookMapper` already handles `deactivated_at`, no changes needed
- [x] 8. Repository implementation — existing; no new methods required
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — **add** `BookAlreadyDeactivatedError → (409, ErrorCode.BOOK_ALREADY_DEACTIVATED)`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — **add** `BOOK_ALREADY_DEACTIVATED`
- [x] 11. Pydantic schemas (`app/presentation/schemas/book_schema.py`) — **add** `DeactivateBookResponse(BaseBookResponse)`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/book_routes.py`) — **add** `PATCH /{book_id}/deactivate`
- [x] 13. Wire in `deps.py` — existing; `BookRepo`, `AdminUser`, and `DbSession` already wired, no changes needed
- [x] 14. Alembic migration — **not required** (no schema change)
- [x] 15. Bruno test files (`bruno/book/deactivate_book/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_deactivate_book.py`)
