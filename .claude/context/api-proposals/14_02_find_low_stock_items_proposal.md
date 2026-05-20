# Admin — Inventory Dashboard — Find Low Stock Items Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 14. Admin — Inventory Dashboard |
| Use Case     | 2. Find Low Stock Items         |
| File Index   | 14_02                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                             |
| ------ | --------------------------------- |
| Method | GET                               |
| URL    | `/api/app/v1/inventory/low-stock` |
| Auth   | Bearer token (ADMIN role)         |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type    | Required | Default                   | Description                                                                            |
| --------- | ------- | -------- | ------------------------- | -------------------------------------------------------------------------------------- |
| threshold | integer | No       | `LOW_STOCK_THRESHOLD` (5) | Upper bound (inclusive) of `stock_quantity` for low-stock classification. Must be ≥ 1. |
| page      | integer | No       | 1                         | Page number (1-based, ≥ 1)                                                             |
| page_size | integer | No       | 20                        | Items per page (1–100)                                                                 |
| sort      | string  | No       | `stock_quantity` (asc)    | Sort expression, e.g. `-stock_quantity` for descending. Parsed by `parse_sort()`.      |

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
        "id": "01932abc-dead-beef-0000-0123456789ab",
        "title": "The Great Gatsby",
        "price": "12.99",
        "language": "English",
        "stock_quantity": 2,
        "cover_url": "books/cover/01932abc.jpg",
        "isbn": "9780743273565",
        "description": "...",
        "page_count": 180,
        "published_date": "1925-04-10",
        "is_active": true,
        "publisher": { "id": "...", "name": "Scribner" },
        "category": { "id": "...", "name": "Fiction" },
        "authors": [
          { "id": "...", "name": "F. Scott Fitzgerald", "display_order": 1 }
        ],
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-10T00:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 25,
      "total_pages": 2,
      "has_next": true,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-dead-beef-0000-0123456789ab",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

Items are ordered by `stock_quantity ASC` by default (most critical first). Books with `stock_quantity = 0` are excluded — they are out-of-stock, not low-stock.

### Error Responses

| HTTP Status | Error Code            | Condition                                                                    |
| ----------- | --------------------- | ---------------------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID    | No Authorization header, token invalid/expired, or token revoked             |
| 403         | ADMIN_ACCESS_REQUIRED | Authenticated user does not have ADMIN role                                  |
| 422         | UNPROCESSABLE_ENTITY  | `threshold < 1`, `page < 1`, `page_size` out of range, or non-integer values |

---

## Procedures

1. The `AdminUser` dependency in `deps.py` validates the Bearer JWT via `JWTService`, checks the blocklist via `RedisCacheService`, loads the user via `IUserRepository.find_by_id()`, and asserts `user.role == UserRole.ADMIN`. If any check fails, `deps.py` raises `HTTPException` (401 or 403) before the use case is reached.

2. FastAPI validates the query parameters via `LowStockQueryRequest` (a Pydantic model). `threshold` defaults to `LOW_STOCK_THRESHOLD` (imported from `app.core.constants`); `page` defaults to 1; `page_size` defaults to 20; `sort` defaults to `None` (the repository applies `stock_quantity ASC` as a fixed default). Pydantic returns HTTP 422 automatically on validation failure.

3. The route handler constructs a `FindLowStockItemsCommand` from the request (building a `QueryParams` with `PageParams` and `parse_sort(sort)`) and instantiates `FindLowStockItemsUseCase(db_session=db_session, book_repo=book_repo)`, then calls `await use_case.execute(cmd)`.

4. The use case calls `await self._book_repo.find_low_stock(query=cmd.query_params, threshold=cmd.threshold)`, returning `PaginatedResult[BookEntity]`.

5. The repository implementation executes two SQL queries against `BookModel` rows where `deleted_at IS NULL`:
   - Count query: `COUNT(*) WHERE stock_quantity > 0 AND stock_quantity <= :threshold`
   - Data query: `SELECT * WHERE stock_quantity > 0 AND stock_quantity <= :threshold ORDER BY stock_quantity ASC LIMIT :page_size OFFSET (:page - 1) * :page_size`

   Each `BookModel` row is converted to a `BookEntity` via `BookMapper.to_entity()`. The result is returned as `PaginatedResult[BookEntity]`. The repository does **not** call `commit()`.

6. The use case maps each `BookEntity` to a `BaseBookResult` using the inherited `_to_result(book, BaseBookResult)` helper from `BaseBookUseCase`, then returns `PaginatedResult[BaseBookResult](items=[...], total_items=result.total_items, page=result.page, page_size=result.page_size)`. No `commit()` is called — this is a pure read operation.

7. The route handler builds the final response as `PaginatedResponse[BaseBookResponse](items=[build_base_book_response(b, BaseBookResponse) for b in result.items], pagination=PaginationMeta.from_result(result))`. `ResponseFormatterMiddleware` wraps it in the `{success, data, meta}` envelope.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                           |
| ------------ | ------ | ----------------------------------------------- |
| `BookEntity` | Read   | Filtered by `stock_quantity` range; no mutation |

### Repository Methods Required

| Interface         | Method                                                                              | New?          |
| ----------------- | ----------------------------------------------------------------------------------- | ------------- |
| `IBookRepository` | `find_all(query: QueryParams, filters: BookFilters)`                                | No (existing) |
| `IBookRepository` | `find_low_stock(query: QueryParams, threshold: int) -> PaginatedResult[BookEntity]` | **Yes**       |

### New DTOs

| DTO Class                  | Type            | Fields                                        |
| -------------------------- | --------------- | --------------------------------------------- |
| `FindLowStockItemsCommand` | Command (input) | `query_params: QueryParams`, `threshold: int` |

File: `app/application/dtos/inventory_dtos.py`

No new result DTO — the use case returns `PaginatedResult[BaseBookResult]` from `app.application.dtos.book_dto`, the same type as `FindBooksUseCase`.

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/inventory/02_find_low_stock_items/`

**`01_success.bru` — Happy Path:**

- [ ] Status 200 OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.items` is an array
- [ ] Each item has `id`, `title`, `stock_quantity` (≥ 1 and ≤ 5), `price`, `authors`, `publisher`, `category`
- [ ] `res.body.data.pagination.total_items` is a non-negative integer
- [ ] `res.body.data.pagination.page` equals 1
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] `02_invalid_threshold.bru` — Status 422 when `threshold=0` → `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_low_stock_items.py`

**Happy Path:**

- [ ] `FindLowStockItemsUseCase.execute(valid_command)` returns `PaginatedResult[BaseBookResult]` with correct `items`, `total_items`, `page`, `page_size`

**Edge Cases:**

- [ ] Returns `PaginatedResult` with empty `items` and `total_items=0` when the fake repository returns no low-stock books
- [ ] Books with `stock_quantity = 0` are **not** included (out-of-stock is excluded by the `> 0` filter in the repository)
- [ ] A book with `stock_quantity` equal to exactly `threshold` **is** included (upper bound is inclusive)
- [ ] A book with `stock_quantity` equal to `threshold + 1` is **not** included

---

## Implementation Checklist

- [ ] 1. Add `FindLowStockItemsCommand` frozen dataclass to `app/application/dtos/inventory_dtos.py`
- [ ] 2. Add `find_low_stock(query: QueryParams, threshold: int) -> PaginatedResult[BookEntity]` abstract method to `IBookRepository` (`app/domain/repositories/book_repository.py`)
- [ ] 3. Create `FindLowStockItemsUseCase` at `app/application/use_cases/inventory/find_low_stock_items.py` — extends `BaseBookUseCase`; returns `PaginatedResult[BaseBookResult]`
- [ ] 4. Export `FindLowStockItemsUseCase` from `app/application/use_cases/inventory/__init__.py`
- [ ] 5. Implement `find_low_stock()` in `BookRepositoryImpl` (`app/infrastructure/db/repositories/book_repository_impl.py`) — count + paginated data queries with `0 < stock_quantity <= threshold`, ordered `stock_quantity ASC`
- [ ] 6. Add `LowStockQueryRequest` Pydantic schema to `app/presentation/schemas/inventory_schema.py` (extends `ListQueryRequest`; adds `threshold: int = Field(default=LOW_STOCK_THRESHOLD, ge=1)`)
- [ ] 7. Add `GET /inventory/low-stock` route handler to `app/presentation/api/app_api/v1/inventory_routes.py` — `response_model=PaginatedResponse[BaseBookResponse]`
- [ ] 8. No new `deps.py` wiring — `BookRepo` and `AdminUser` are already wired by `GET /inventory/metrics`
- [ ] 9. No new exception mapping or error codes
- [ ] 10. No Alembic migration — no schema change
- [ ] 11. Bruno test files: `bruno/inventory/02_find_low_stock_items/folder.bru` + `01_success.bru` + one file per error case
- [ ] 12. Pytest unit tests: `backend/tests/unit/test_find_low_stock_items.py`
