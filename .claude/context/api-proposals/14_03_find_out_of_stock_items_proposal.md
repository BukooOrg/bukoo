# Admin — Inventory Dashboard — Find Out Of Stock Items Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 14. Admin — Inventory Dashboard |
| Use Case     | 3. Find Out Of Stock Items      |
| File Index   | 14_03                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                                |
| ------ | ------------------------------------ |
| Method | GET                                  |
| URL    | `/api/app/v1/inventory/out-of-stock` |
| Auth   | Bearer token (ADMIN role)            |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type    | Required | Default | Description                      |
| --------- | ------- | -------- | ------- | -------------------------------- |
| page      | integer | No       | 1       | Page number (≥ 1)                |
| page_size | integer | No       | 20      | Items per page (1–100)           |
| sort      | string  | No       | None    | Sort expression e.g. `title:asc` |

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
    "items": [
      {
        "id": "01932abc-...",
        "title": "The Great Gatsby",
        "price": "14.99",
        "stock_quantity": 0,
        "language": "English",
        "isbn": "9780743273565",
        "cover_url": null,
        "description": "A novel by F. Scott Fitzgerald.",
        "page_count": 180,
        "published_date": "1925-04-10",
        "is_active": true,
        "publisher": { "id": "01932abc-...", "name": "Scribner" },
        "category": { "id": "01932abc-...", "name": "Fiction" },
        "authors": [
          {
            "id": "01932abc-...",
            "name": "F. Scott Fitzgerald",
            "display_order": 1
          }
        ],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                   |
| ----------- | -------------------- | ------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No Authorization header or invalid JWT      |
| 401         | AUTH_TOKEN_EXPIRED   | JWT has expired                             |
| 403         | PERMISSION_DENIED    | Authenticated user does not have ADMIN role |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure on query params |

---

## Procedures

1. **Auth/guard** — `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the revocation blocklist in Redis, loads the `UserEntity`, and asserts `role == UserRole.ADMIN`. Raises HTTP 401/403 on failure — handled entirely by the dependency, not the use case.

2. **Input validation** — FastAPI deserializes `page`, `page_size`, and `sort` from the query string into a `ListQueryRequest` instance via `Depends()`. Pydantic returns HTTP 422 automatically if constraints are violated.

3. **Build command** — The route handler constructs `FindOutOfStockItemsCommand(query_params=QueryParams(page=PageParams(...), sorts=parse_sort(query.sort)))`.

4. **Repository query** — `FindOutOfStockItemsUseCase.execute()` calls `self._book_repo.find_out_of_stock(query=cmd.query_params)`. The repository implementation selects non-deleted `BookModel` rows where `stock_quantity == 0`, applies pagination and sort from `QueryParams`, and returns `PaginatedResult[BookEntity]`.

5. **Map to result** — The use case maps each `BookEntity` to `BaseBookResult` via `self._to_result(b, BaseBookResult)` (inherited from `BaseBookUseCase`), and returns `PaginatedResult[BaseBookResult]`.

6. **Return** — The route handler maps each `BaseBookResult` to `BaseBookResponse` via `build_base_book_response(b, BaseBookResponse)`, wraps them in `PaginatedResponse`, and returns it. `ResponseFormatterMiddleware` wraps the response in the `{success, data, meta}` envelope.

No mutations occur; `await self._db_session.commit()` is not called.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                               |
| ------------ | ------ | --------------------------------------------------- |
| `BookEntity` | Read   | Filter: `stock_quantity == 0`, `deleted_at IS NULL` |

### Repository Methods Required

| Interface         | Method                                                                 | New? |
| ----------------- | ---------------------------------------------------------------------- | ---- |
| `IBookRepository` | `find_out_of_stock(query: QueryParams) -> PaginatedResult[BookEntity]` | Yes  |

### New DTOs

| DTO Class                    | Type            | Fields                      |
| ---------------------------- | --------------- | --------------------------- |
| `FindOutOfStockItemsCommand` | Command (input) | `query_params: QueryParams` |

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/inventory/03_find_out_of_stock_items/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] Every item in `res.body.data.items` has `stock_quantity == 0`
- [x] `res.body.data.pagination.page` equals 1
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_out_of_stock_items.py`

**Happy Path:**

- [x] `FindOutOfStockItemsUseCase.execute(cmd)` returns `PaginatedResult[BaseBookResult]` where all items have `stock_quantity == 0`

**Edge Cases:**

- [x] Returns empty paginated result when no books are out of stock
- [x] Passes `QueryParams` (page/sort) through to the repository unmodified
- [x] Returns correct `total_items`, `total_pages`, `has_next`, `has_prev` from paginated result

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/`) — existing `BookEntity`
- [x] 2. Domain exceptions (`app/domain/exceptions/`) — none needed
- [x] 3. Repository interface — add `find_out_of_stock(query: QueryParams) -> PaginatedResult[BookEntity]` to `IBookRepository` in `app/domain/repositories/book_repository.py`
- [x] 4. DTOs — add `FindOutOfStockItemsCommand` to `app/application/dtos/inventory_dtos.py`
- [x] 5. Use case — `app/application/use_cases/inventory/find_out_of_stock_items.py` (`FindOutOfStockItemsUseCase`); export from `app/application/use_cases/inventory/__init__.py`
- [x] 6. ORM model — no new model needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — implement `find_out_of_stock` in `app/infrastructure/db/repositories/book_repository_impl.py`
- [x] 9. Exception mapping — none needed
- [x] 10. Error codes — none needed
- [x] 11. Pydantic schemas — use `ListQueryRequest` directly (no new schema needed)
- [x] 12. Route handler — add `GET /out-of-stock` handler to `app/presentation/api/app_api/v1/inventory_routes.py`
- [x] 13. Wire in `deps.py` — already wired via existing `BookRepo` alias
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/inventory/03_find_out_of_stock_items/folder.bru` + `01_success.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_out_of_stock_items.py`
