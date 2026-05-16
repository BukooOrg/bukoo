# Order API Set — View Order Detail Proposal

## Overview

| Field        | Value                |
| ------------ | -------------------- |
| API Set      | 11. Order            |
| Use Case     | 4. View Order Detail |
| File Index   | 11_04                |
| Access Level | 👤🔑 Both            |
| Status       | Implemented          |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | GET                                     |
| URL    | `/api/app/v1/orders/{order_id}`         |
| Auth   | Bearer token (any role — USER or ADMIN) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter  | Type          | Description              |
| ---------- | ------------- | ------------------------ |
| `order_id` | string (UUID) | ID of the order to fetch |

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
    "id": "01932abc-0000-7000-8000-000000000001",
    "user_id": "01932abc-0000-7000-8000-000000000010",
    "status": "paid",
    "subtotal": "39.98",
    "shipping_cost": "5.00",
    "total": "44.98",
    "address_snapshot": {
      "street": "123 Main St",
      "city": "Kuala Lumpur",
      "state": "WP",
      "postcode": "50000",
      "country": "Malaysia"
    },
    "items": [
      {
        "id": "01932abc-0000-7000-8000-000000000100",
        "book_id": "01932abc-0000-7000-8000-000000000200",
        "book_title": "Clean Architecture",
        "unit_price": "19.99",
        "quantity": 2,
        "line_total": "39.98"
      }
  x],
    "payment": {
      "id": "01932abc-0000-7000-8000-000000000300",
      "method": "card",
      "amount": "44.98",
      "status": "success",
      "simulated_ref": "SIM-ABC123",
      "created_at": "2026-01-15T10:32:00Z"
    },
    "created_at": "2026-01-15T10:30:00Z",
    "updated_at": "2026-01-15T10:32:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:32:05Z"
  }
}
```

> `payment` is `null` when the order has not yet been paid (status is `PENDING`).

### Error Responses

| HTTP Status | Error Code            | Condition                                                 |
| ----------- | --------------------- | --------------------------------------------------------- |
| 401         | `UNAUTHORIZED`        | No Authorization header provided                          |
| 401         | `TOKEN_EXPIRED`       | Bearer token is expired                                   |
| 401         | `INVALID_TOKEN`       | Bearer token is malformed or invalid                      |
| 403         | `ORDER_ACCESS_DENIED` | Authenticated customer is requesting another user's order |
| 404         | `ORDER_NOT_FOUND`     | No order exists for the given `order_id`                  |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and returns the active `UserEntity`. Both `UserRole.USER` and `UserRole.ADMIN` are accepted.
2. **Fetch order** — Call `order_repo.find_by_id(order_id)`. If the result is `None`, raise `OrderNotFoundError(order_id)`.
3. **Ownership check** — If `current_user.role == UserRole.USER` and `order.user_id != current_user.id`, raise `OrderAccessDeniedError(order_id)`. Admin users skip this check.
4. **Extract payment** — Take `order.payments[0]` if the list is non-empty, otherwise set `payment = None`.
5. **Return result** — Construct and return `ViewOrderDetailResult` with all order fields, the full items list, and the resolved payment (or `None`).

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                                          |
| ----------------- | ------ | -------------------------------------------------------------- |
| `OrderEntity`     | Read   | Includes `_order_items` and `_payments` (both selectin-loaded) |
| `OrderItemEntity` | Read   | Accessed via `order.order_items`                               |
| `PaymentEntity`   | Read   | Accessed via `order.payments[0]` if present                    |

### Repository Methods Required

| Interface          | Method                 | New?          |
| ------------------ | ---------------------- | ------------- |
| `IOrderRepository` | `find_by_id(order_id)` | No (existing) |

### New DTOs

| DTO Class                | Type            | Fields                                                                                                                                                                                                                             |
| ------------------------ | --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ViewOrderDetailCommand` | Command (input) | `order_id: str`, `user_id: str`, `user_role: UserRole`                                                                                                                                                                             |
| `ViewOrderDetailResult`  | Result (output) | `id`, `user_id`, `status: OrderStatus`, `subtotal`, `shipping_cost`, `total: Decimal`, `address_snapshot: dict`, `items: list[BaseOrderItemResult]`, `payment: PaymentSummaryResult \| None`, `created_at`, `updated_at: datetime` |

> `BaseOrderItemResult` and `PaymentSummaryResult` already exist in `order_dto.py` and `payment_dto.py` respectively — reuse them.

### New Domain Exceptions

| Exception Class          | File                             | Inherits          |
| ------------------------ | -------------------------------- | ----------------- |
| `OrderAccessDeniedError` | `app/domain/exceptions/order.py` | `DomainException` |

### New Error Codes

| Constant              | Value                   | Description                                     |
| --------------------- | ----------------------- | ----------------------------------------------- |
| `ORDER_ACCESS_DENIED` | `"ORDER_ACCESS_DENIED"` | Customer attempted to view another user's order |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/order/view_order_detail/`

**`01_success_customer.bru` — Happy Path (customer views own order):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` equals the requested `order_id`
- [x] `res.body.data.items` is a non-empty array
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when `order_id` does not exist → error code `ORDER_NOT_FOUND`
- [x] `03_access_denied.bru` — Status 403 when customer requests another user's order → error code `ORDER_ACCESS_DENIED`
- [x] `04_success_admin.bru` — Status 200 when admin requests any order (including one not belonging to them)

### Pytest Unit Tests

**File:** `backend/tests/unit/test_view_order_detail.py`

**Happy Path:**

- [x] `ViewOrderDetailUseCase.execute(valid_command_customer)` returns `ViewOrderDetailResult` with correct `id`, `status`, `items`, and `payment` fields when user owns the order
- [x] `ViewOrderDetailUseCase.execute(valid_command_admin)` returns `ViewOrderDetailResult` for an order owned by a different user

**Error Cases:**

- [x] Raises `OrderNotFoundError` when `order_repo.find_by_id` returns `None`
- [x] Raises `OrderAccessDeniedError` when `user_role == UserRole.USER` and `order.user_id != command.user_id`

**Edge Cases:**

- [x] `payment` field in result is `None` when `order.payments` list is empty (PENDING order)
- [x] Admin with `user_id != order.user_id` does NOT raise `OrderAccessDeniedError`

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/`) — _existing: `OrderEntity`, `OrderItemEntity`, `PaymentEntity`_
- [x] 2. Domain exceptions (`app/domain/exceptions/order.py`) — _new: `OrderAccessDeniedError`; export in `__init__.py`_
- [x] 3. Repository interface method(s) — _existing: `IOrderRepository.find_by_id`_
- [x] 4. DTOs (`app/application/dtos/order_dto.py`) — _new: `ViewOrderDetailCommand`, `ViewOrderDetailResult`_
- [x] 5. Use case (`app/application/use_cases/order/view_order_detail.py`) — _new: `ViewOrderDetailUseCase`_
- [x] 6. ORM model — _no change needed_
- [x] 7. Mapper — _no change needed_
- [x] 8. Repository implementation — _no change needed_
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — _add `OrderAccessDeniedError` → 403, `ORDER_ACCESS_DENIED`_
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — _add `ORDER_ACCESS_DENIED`_
- [x] 11. Pydantic schemas (`app/presentation/schemas/order_schema.py`) — _new: `OrderDetailResponse`_
- [x] 12. Route handler (`app/presentation/api/app_api/v1/order_routes.py`) — _add `GET /{order_id}` handler_
- [x] 13. Wire in `deps.py` — _existing: `CurrentUser`, `OrderRepo` already wired_
- [x] 14. Alembic migration — _not needed (no schema change)_
- [x] 15. Bruno test files (`bruno/order/03_view_order_detail/` — `folder.bru` + 4 test files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_view_order_detail.py`)
