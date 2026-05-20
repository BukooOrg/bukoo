# Admin — Inventory Dashboard — Get Inventory Metrics Proposal

## Overview

| Field        | Value                           |
| ------------ | ------------------------------- |
| API Set      | 14. Admin — Inventory Dashboard |
| Use Case     | 1. Get Inventory Metrics        |
| File Index   | 14_01                           |
| Access Level | 🔑 Admin                        |
| Status       | Implemented                     |

---

## Endpoint

| Field  | Value                           |
| ------ | ------------------------------- |
| Method | GET                             |
| URL    | `/api/app/v1/inventory/metrics` |
| Auth   | Bearer token (ADMIN role)       |

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
    "total_sku_count": 150,
    "out_of_stock_count": 12,
    "low_stock_count": 25,
    "total_inventory_value": "15234.50"
  },
  "meta": {
    "requestId": "01932abc-dead-beef-0000-0123456789ab",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

**Field semantics:**

| Field                   | Type             | Definition                                                                                                       |
| ----------------------- | ---------------- | ---------------------------------------------------------------------------------------------------------------- |
| `total_sku_count`       | integer          | COUNT of all non-deleted books (`deleted_at IS NULL`), including deactivated                                     |
| `out_of_stock_count`    | integer          | COUNT of non-deleted books where `stock_quantity = 0`                                                            |
| `low_stock_count`       | integer          | COUNT of non-deleted books where `0 < stock_quantity <= LOW_STOCK_THRESHOLD`                                     |
| `total_inventory_value` | string (Decimal) | `SUM(price × stock_quantity)` across all non-deleted books; serialized as a decimal string to preserve precision |

> **Note on `LOW_STOCK_THRESHOLD`:** A new integer constant `LOW_STOCK_THRESHOLD = 5` is added to `app/core/constants.py`. It defines the upper bound (inclusive) for low-stock classification. The three stock states are mutually exclusive: out-of-stock (`qty = 0`), low-stock (`0 < qty ≤ threshold`), and normal (`qty > threshold`).

### Error Responses

| HTTP Status | Error Code            | Condition                                                        |
| ----------- | --------------------- | ---------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID    | No Authorization header, token invalid/expired, or token revoked |
| 403         | ADMIN_ACCESS_REQUIRED | Authenticated user does not have ADMIN role                      |

---

## Procedures

1. The `AdminUser` dependency in `deps.py` validates the Bearer JWT via `JWTService`, checks the blocklist via `RedisCacheService`, loads the user via `IUserRepository.find_by_id()`, and asserts `user.role == UserRole.ADMIN`. If any check fails, `deps.py` raises `HTTPException` (401 or 403) before the use case is reached.

2. The route handler instantiates `GetInventoryMetricsUseCase(db_session=db_session, book_repo=book_repo)` and calls `await use_case.execute()` with no command argument.

3. The use case calls `await self._book_repo.get_inventory_metrics(low_stock_threshold=LOW_STOCK_THRESHOLD)`. `LOW_STOCK_THRESHOLD` is imported from `app.core.constants`.

4. The repository implementation executes a single SQL aggregate query over `BookModel` rows where `deleted_at IS NULL`:
   - `total_sku_count = COUNT(*)`
   - `out_of_stock_count = COUNT(*) FILTER (WHERE stock_quantity = 0)` (or equivalent conditional expression)
   - `low_stock_count = COUNT(*) FILTER (WHERE stock_quantity > 0 AND stock_quantity <= :threshold)`
   - `total_inventory_value = COALESCE(SUM(price * stock_quantity), 0)`

   The query returns a single row. The result is mapped to a `BookInventoryMetrics` dataclass and returned. The repository does **not** call `commit()`.

5. The use case builds and returns `GetInventoryMetricsResult(total_sku_count=metrics.total_sku_count, out_of_stock_count=metrics.out_of_stock_count, low_stock_count=metrics.low_stock_count, total_inventory_value=metrics.total_inventory_value)`. No `commit()` is called — this is a pure read operation.

6. The route handler returns the result DTO. `ResponseFormatterMiddleware` wraps it in the `{success, data, meta}` envelope before sending to the client.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                           |
| ------------ | ------ | ----------------------------------------------- |
| `BookEntity` | Read   | Aggregated at the DB level; no entity hydration |

### New Constants

| Constant              | File                    | Value | Description                                                                      |
| --------------------- | ----------------------- | ----- | -------------------------------------------------------------------------------- |
| `LOW_STOCK_THRESHOLD` | `app/core/constants.py` | `5`   | Upper bound (inclusive) for low-stock classification. Shared with endpoint 14.2. |

### Repository Methods Required

| Interface         | Method                                                                    | New?          |
| ----------------- | ------------------------------------------------------------------------- | ------------- |
| `IBookRepository` | `find_all(query, filters)`                                                | No (existing) |
| `IBookRepository` | `get_inventory_metrics(low_stock_threshold: int) -> BookInventoryMetrics` | **Yes**       |

**New supporting type — `BookInventoryMetrics`** (defined alongside `IBookRepository` in `app/domain/repositories/book_repository.py`):

```python
@dataclass(frozen=True)
class BookInventoryMetrics:
    total_sku_count: int
    out_of_stock_count: int
    low_stock_count: int
    total_inventory_value: Decimal
```

### New DTOs

| DTO Class                   | Type            | Fields                                                                                                      |
| --------------------------- | --------------- | ----------------------------------------------------------------------------------------------------------- |
| `GetInventoryMetricsResult` | Result (output) | `total_sku_count: int`, `out_of_stock_count: int`, `low_stock_count: int`, `total_inventory_value: Decimal` |

File: `app/application/dtos/inventory_dtos.py`

### New Domain Exceptions

_(None — the only failure modes are auth-related and are handled entirely by `deps.py` as `HTTPException`.)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/14_admin_inventory_dashboard/get_inventory_metrics/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.total_sku_count` is a non-negative integer
- [x] `res.body.data.out_of_stock_count` is a non-negative integer
- [x] `res.body.data.low_stock_count` is a non-negative integer
- [x] `res.body.data.total_inventory_value` is a string parseable as a decimal ≥ 0
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_inventory_metrics.py`

**Happy Path:**

- [x] `GetInventoryMetricsUseCase.execute()` returns `GetInventoryMetricsResult` with `total_sku_count`, `out_of_stock_count`, `low_stock_count`, and `total_inventory_value` matching the values returned by the fake repository.

**Edge Cases:**

- [x] Returns all-zero metrics (zeros for counts, `Decimal("0")` for value) when the fake repository returns an empty inventory (no books in the catalogue).
- [x] `low_stock_count` includes only books with `0 < stock_quantity <= LOW_STOCK_THRESHOLD`; books at exactly `LOW_STOCK_THRESHOLD` are included; books at `LOW_STOCK_THRESHOLD + 1` are excluded.
- [x] A book with `stock_quantity = 0` is counted in `out_of_stock_count` and not in `low_stock_count`.

---

## Implementation Checklist

- [x] 1. Add `LOW_STOCK_THRESHOLD: int = 5` to `app/core/constants.py`
- [x] 2. Add `BookInventoryMetrics` frozen dataclass to `app/domain/repositories/book_repository.py`
- [x] 3. Add `get_inventory_metrics(low_stock_threshold: int) -> BookInventoryMetrics` abstract method to `IBookRepository`
- [x] 4. Add `GetInventoryMetricsResult` frozen dataclass to `app/application/dtos/inventory_dtos.py`
- [x] 5. Create `GetInventoryMetricsUseCase` at `app/application/use_cases/inventory/get_inventory_metrics.py`
- [x] 6. Implement `get_inventory_metrics()` in `BookRepositoryImpl` (`app/infrastructure/db/repositories/book_repository_impl.py`) — single SQL aggregate query
- [x] 7. Add `InventoryMetricsResponse` Pydantic schema to `app/presentation/schemas/inventory_schema.py`
- [x] 8. Create route handler `GET /inventory/metrics` in `app/presentation/api/app_api/v1/inventory_routes.py`
- [x] 9. Register `inventory_routes` in `app/presentation/api/app_api/v1/__init__.py`
- [x] 10. No new `deps.py` wiring needed — `BookRepo` alias is already used by existing book endpoints
- [x] 11. No Alembic migration — no schema change
- [x] 12. Bruno test files: `folder.bru` + `01_success.bru`
- [x] 13. Pytest unit tests: `backend/tests/unit/test_get_inventory_metrics.py`
