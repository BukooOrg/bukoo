# Order API Set — Find Orders Proposal

## Overview

| Field        | Value          |
| ------------ | -------------- |
| API Set      | 11. Order      |
| Use Case     | 3. Find Orders |
| File Index   | 11_03          |
| Access Level | 👤🔑 Both      |
| Status       | Implemented    |

---

## Endpoint

| Field  | Value                   |
| ------ | ----------------------- |
| Method | GET                     |
| URL    | `/api/app/v1/orders`    |
| Auth   | Bearer token (any role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter   | Type        | Required | Default | Description                                                                    |
| ----------- | ----------- | -------- | ------- | ------------------------------------------------------------------------------ |
| `page`      | integer     | No       | 1       | Page number (1-based)                                                          |
| `limit`     | integer     | No       | 20      | Items per page (max 100)                                                       |
| `status`    | OrderStatus | No       | —       | Filter by order status: `pending`, `paid`, `shipped`, `delivered`, `cancelled` |
| `user_id`   | string      | No       | —       | **Admin only** — filter by a specific user's orders; ignored for customers     |
| `date_from` | date        | No       | —       | Filter orders created on or after this date (ISO 8601: `YYYY-MM-DD`)           |
| `date_to`   | date        | No       | —       | Filter orders created on or before this date (ISO 8601: `YYYY-MM-DD`)          |

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
        "user_id": "01932abc-...",
        "status": "paid",
        "total": "125.00",
        "item_count": 3,
        "created_at": "2026-01-15T10:30:00Z",
        "updated_at": "2026-01-15T11:00:00Z"
      }
    ],
    "total": 45,
    "page": 1,
    "limit": 20,
    "pages": 3
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code         | Condition                                              |
| ----------- | ------------------ | ------------------------------------------------------ |
| 401         | `UNAUTHORIZED`     | No Authorization header provided                       |
| 401         | `TOKEN_EXPIRED`    | Bearer token is expired                                |
| 401         | `INVALID_TOKEN`    | Bearer token is malformed or invalid                   |
| 422         | `VALIDATION_ERROR` | Pydantic validation failure (e.g., invalid page value) |

---

## Procedures

1. **Auth guard** — Validate the Bearer token via the `CurrentUser` dependency in `deps.py`. Returns a `UserEntity`; raises HTTP 401 on token failure.
2. **Build effective filters** — If `user.role == UserRole.USER`, force `effective_user_id = user.id` and ignore any `user_id` query parameter. If `user.role == UserRole.ADMIN`, use the provided `user_id` query param as-is (may be `None` to retrieve all users' orders).
3. **Query repository** — Call `await self._order_repo.find_many(user_id=effective_user_id, status=cmd.status, date_from=cmd.date_from, date_to=cmd.date_to, offset=(cmd.page - 1) * cmd.limit, limit=cmd.limit)`, which returns a `tuple[list[OrderEntity], int]` — the page of entities and the total count matching the filters.
4. **Map to result** — Build a `FindOrdersResult` containing a `list[OrderSummaryResult]` (one per entity) and pagination metadata (`total`, `page`, `limit`, `pages = ceil(total / limit)`). `OrderSummaryResult` is a lightweight read model: `id`, `user_id`, `status`, `total`, `item_count = len(order.order_items)`, `created_at`, `updated_at`.
5. **Return** — Return the `FindOrdersResult`; no commit is needed (read-only operation).

---

## Domain Impact

### Entities Involved

| Entity        | Access | Notes                                                          |
| ------------- | ------ | -------------------------------------------------------------- |
| `OrderEntity` | Read   | Loaded in pages; `order_items` eagerly loaded for `item_count` |

### Repository Methods Required

| Interface          | Method                                                                                           | New? |
| ------------------ | ------------------------------------------------------------------------------------------------ | ---- |
| `IOrderRepository` | `find_many(user_id, status, date_from, date_to, offset, limit) -> tuple[list[OrderEntity], int]` | Yes  |

### New DTOs

| DTO Class            | Type            | Fields                                                                                                                                                                                |
| -------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `FindOrdersCommand`  | Command (input) | `requester_id: str`, `requester_role: UserRole`, `page: int`, `limit: int`, `status: OrderStatus \| None`, `user_id: str \| None`, `date_from: date \| None`, `date_to: date \| None` |
| `OrderSummaryResult` | Result (output) | `id: str`, `user_id: str \| None`, `status: OrderStatus`, `total: Decimal`, `item_count: int`, `created_at: datetime`, `updated_at: datetime`                                         |
| `FindOrdersResult`   | Result (output) | `items: list[OrderSummaryResult]`, `total: int`, `page: int`, `limit: int`, `pages: int`                                                                                              |

### New Domain Exceptions

_(None — no new exceptions needed)_

### New Error Codes

_(None — no new error codes needed)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/order/03_find_orders/`

**`01_success.bru` — Customer sees only own orders:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.total`, `page`, `limit`, `pages` are present

**`02_success_admin_filter_by_user.bru` — Admin filters by `user_id`:**

- [x] Status 200 OK
- [x] All items in response belong to the specified user

**`03_success_filter_by_status.bru` — Filter by `status=paid`:**

- [x] Status 200 OK
- [x] All `res.body.data.items[*].status` equal `"paid"`

**`04_success_filter_by_date_range.bru` — Filter by `date_from` + `date_to`:**

- [x] Status 200 OK
- [x] All `res.body.data.items[*].created_at` fall within the specified range

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_orders.py`

**Happy Path:**

- [x] `FindOrdersUseCase.execute(valid_command)` returns `FindOrdersResult` with correct `items` and pagination fields
- [x] Customer role forces `user_id` filter to `requester_id` regardless of command `user_id`
- [x] Admin role with no `user_id` filter returns all orders from the fake repo

**Filter Cases:**

- [x] `status` filter is passed through to `repo.find_many`
- [x] `date_from` / `date_to` filters are passed through to `repo.find_many`
- [x] `pages` is correctly computed as `ceil(total / limit)`

**Edge Cases:**

- [x] Empty result set returns `items=[]`, `total=0`, `pages=0`
- [x] `page=1, limit=20` with `total=0` returns `pages=0`

---

## Implementation Checklist

- [x] 1. Domain entity — `OrderEntity` (existing)
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface method — add `find_many(...)` to `IOrderRepository`
- [x] 4. DTOs — add `FindOrdersCommand`, `OrderSummaryResult`, `FindOrdersResult` to `app/application/dtos/order_dto.py`
- [x] 5. Use case — `app/application/use_cases/order/find_orders.py`
- [x] 6. ORM model — `OrderModel` (existing)
- [x] 7. Mapper — `OrderMapper` (existing)
- [x] 8. Repository implementation — add `find_many(...)` to `OrderRepositoryImpl`
- [x] 9. Exception mapping — no changes
- [x] 10. Error codes — no new codes
- [x] 11. Pydantic schemas — add `FindOrdersResponse`, `OrderSummaryResponse` to `app/presentation/schemas/order_schema.py`
- [x] 12. Route handler — add `GET /orders` to `app/presentation/api/app_api/v1/order_routes.py`
- [x] 13. Wire in `deps.py` — `OrderRepo` alias already exists; no new wiring needed
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files — `bruno/order/03_find_orders/` + 4 `.bru` files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_orders.py`
