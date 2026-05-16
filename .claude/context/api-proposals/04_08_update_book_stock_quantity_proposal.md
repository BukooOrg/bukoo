# Book Catalog — Update Book Stock Quantity Proposal

## Overview

| Field        | Value                         |
| ------------ | ----------------------------- |
| API Set      | 4. Book Catalog               |
| Use Case     | 8. Update Book Stock Quantity |
| File Index   | 04_08                         |
| Access Level | 🔑 Admin                      |
| Status       | Implemented                   |

---

## Endpoint

| Field  | Value                               |
| ------ | ----------------------------------- |
| Method | PATCH                               |
| URL    | `/api/app/v1/books/{book_id}/stock` |
| Auth   | Bearer token (ADMIN role)           |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                            |
| --------- | ------------- | -------------------------------------- |
| book_id   | string (UUID) | The ID of the book to update stock for |

### Query Parameters

_(None)_

### Request Body

| Field    | Type    | Required | Constraints                       |
| -------- | ------- | -------- | --------------------------------- |
| quantity | integer | Yes      | `>= 0` — new absolute stock value |

**Example:**

```json
{
  "quantity": 150
}
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
    "title": "The Great Gatsby",
    "price": "12.99",
    "language": "en",
    "stock_quantity": 150,
    "cover_url": null,
    "isbn": "9780743273565",
    "description": null,
    "page_count": 180,
    "published_date": "1925-04-10",
    "is_active": true,
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

| HTTP Status | Error Code              | Condition                                                            |
| ----------- | ----------------------- | -------------------------------------------------------------------- |
| 401         | `NOT_AUTH_HEADER`       | No Authorization header provided                                     |
| 401         | `TOKEN_EXPIRED`         | Bearer token has expired                                             |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or revoked                                 |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user does not have the ADMIN role                      |
| 404         | `BOOK_NOT_FOUND`        | No book found for the given `book_id` (or it is soft-deleted)        |
| 422         | `VALIDATION_ERROR`      | Pydantic validation failure (e.g. `quantity` is negative or missing) |

---

## Procedures

1. **Auth/guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the Redis blocklist for revocation, and asserts `user.role == UserRole.ADMIN`. Raises HTTP 401 or 403 if any check fails. The use case receives no user argument.

2. **Input validation** — Pydantic validates `quantity >= 0` on the request body. FastAPI returns HTTP 422 automatically on failure.

3. **Fetch the book** — Call `await book_repo.find_by_id(command.book_id, BookStatusFilter(status="all"))`. Using `status="all"` allows stock updates on both active and deactivated books, while still excluding soft-deleted records.

4. **Existence check** — If `find_by_id` returns `None`, raise `BookNotFoundError(command.book_id)`. This maps to HTTP 404 / `BOOK_NOT_FOUND`.

5. **Mutate the entity** — Call `book.set_stock(command.quantity)`. The new entity method sets `_stock_quantity = quantity` and `_updated_at = datetime.now(UTC)`.

6. **Persist** — Call `await book_repo.save(book)`. The repository executes `session.merge(model)` but does NOT commit.

7. **Commit** — Call `await self._db_session.commit()` to flush the unit of work.

8. **Return** — Build and return `UpdateBookStockResult` from the mutated `BookEntity`, mapping all fields from `BaseBookResult`. `stock_quantity` will reflect the new value.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes                                                              |
| ------------ | ------------ | ------------------------------------------------------------------ |
| `BookEntity` | Read / Write | New `set_stock(quantity)` method sets `_stock_quantity` absolutely |

### Repository Methods Required

| Interface         | Method                                  | New?          |
| ----------------- | --------------------------------------- | ------------- |
| `IBookRepository` | `find_by_id(book_id, BookStatusFilter)` | No (existing) |
| `IBookRepository` | `save(book)`                            | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                          |
| ------------------------ | --------------- | ------------------------------- |
| `UpdateBookStockCommand` | Command (input) | `book_id: str`, `quantity: int` |
| `UpdateBookStockResult`  | Result (output) | Extends `BaseBookResult`        |

### New Domain Exceptions

_(None — `BOOK_NOT_FOUND` already exists; `quantity >= 0` is enforced by Pydantic)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book/update_book_stock_quantity/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.stock_quantity` equals the `quantity` sent in the request
- [x] `res.body.data.id` equals the book ID used in the request
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when a USER-role token is used → `ADMIN_ACCESS_REQUIRED`
- [x] `03_book_not_found.bru` — Status 404 when `book_id` does not exist → `BOOK_NOT_FOUND`
- [x] `04_invalid_quantity.bru` — Status 422 when `quantity` is negative → `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_book_stock_quantity.py`

**Happy Path:**

- [x] `UpdateBookStockUseCase.execute(valid_command)` returns `UpdateBookStockResult` with `stock_quantity` equal to the commanded value
- [x] Setting `quantity` to `0` succeeds and returns `stock_quantity == 0`

**Error Cases:**

- [x] Raises `BookNotFoundError` when `book_repo.find_by_id` returns `None`

**Edge Cases:**

- [x] Setting `quantity` to the same value as the current stock succeeds (idempotent)
- [x] A soft-deleted book (simulated by the fake repo returning `None`) is treated the same as not-found

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/book_entity.py`) — **add** `set_stock(quantity: int) -> None` method
- [x] 2. Domain exceptions — existing; no new exceptions needed
- [x] 3. Repository interface (`app/domain/repositories/book_repository.py`) — existing; no changes needed
- [x] 4. DTOs (`app/application/dtos/book_dto.py`) — **add** `UpdateBookStockCommand` and `UpdateBookStockResult`
- [x] 5. Use case (`app/application/use_cases/book/update_book_stock.py`) — **new file**; export from `app/application/use_cases/book/__init__.py`
- [x] 6. ORM model — existing; no migration needed
- [x] 7. Mapper — existing; no changes needed
- [x] 8. Repository implementation — existing; no changes needed
- [x] 9. Exception mapping — existing; no changes needed
- [x] 10. Error codes — existing; no changes needed
- [x] 11. Pydantic schemas (`app/presentation/schemas/book_schema.py`) — **add** `UpdateBookStockRequest` and `UpdateBookStockResponse(BaseBookResponse)`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/book_routes.py`) — **add** `PATCH /{book_id}/stock`
- [x] 13. Wire in `deps.py` — existing; `BookRepo`, `AdminUser`, and `DbSession` already wired, no changes needed
- [x] 14. Alembic migration — **not required** (no schema change)
- [x] 15. Bruno test files (`bruno/book/update_book_stock_quantity/` — `folder.bru` + `01_success.bru` + one file per error case)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_update_book_stock_quantity.py`)
