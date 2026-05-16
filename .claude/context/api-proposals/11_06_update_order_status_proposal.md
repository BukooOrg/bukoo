# Order API Set — Update Order Status Proposal

## Overview

| Field        | Value                  |
| ------------ | ---------------------- |
| API Set      | 11. Order              |
| Use Case     | 6. Update Order Status |
| File Index   | 11_06                  |
| Access Level | 🔑 Admin               |
| Status       | Implemented            |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | PATCH                                  |
| URL    | `/api/app/v1/orders/{order_id}/status` |
| Auth   | Bearer token (ADMIN role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter  | Type          | Description                |
| ---------- | ------------- | -------------------------- |
| `order_id` | string (UUID) | ID of the order to advance |

### Query Parameters

_(None)_

### Request Body

| Field    | Type   | Required | Constraints                        |
| -------- | ------ | -------- | ---------------------------------- |
| `status` | string | Yes      | One of: `"shipped"`, `"delivered"` |

**Example:**

```json
{
  "status": "shipped"
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
    "id": "01932abc-0000-7000-8000-000000000001",
    "status": "shipped",
    "updated_at": "2026-01-16T09:00:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-16T09:00:01Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                        | Condition                                                                       |
| ----------- | --------------------------------- | ------------------------------------------------------------------------------- |
| 401         | `UNAUTHORIZED`                    | No Authorization header provided                                                |
| 401         | `TOKEN_EXPIRED`                   | Bearer token is expired                                                         |
| 401         | `INVALID_TOKEN`                   | Bearer token is malformed or invalid                                            |
| 403         | `ADMIN_ACCESS_REQUIRED`           | Authenticated user does not have `ADMIN` role                                   |
| 404         | `ORDER_NOT_FOUND`                 | No order exists for the given `order_id`                                        |
| 409         | `ORDER_STATUS_TRANSITION_INVALID` | The requested `status` is not a valid next step from the order's current status |
| 422         | `VALIDATION_ERROR`                | `status` field is missing or not one of `"shipped"` / `"delivered"`             |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency validates the Bearer token and enforces `UserRole.ADMIN`; non-admin callers receive 403.
2. **Fetch order** — Call `order_repo.find_by_id(order_id)`. If `None`, raise `OrderNotFoundError(order_id)`.
3. **Transition validation** — Check that the requested status is a valid next step:
   - `"shipped"` requires `order.status == OrderStatus.PAID`; otherwise raise `OrderStatusTransitionInvalidError(order_id, order.status, OrderStatus.SHIPPED)`.
   - `"delivered"` requires `order.status == OrderStatus.SHIPPED`; otherwise raise `OrderStatusTransitionInvalidError(order_id, order.status, OrderStatus.DELIVERED)`.
4. **Mutate order** — Call `order.mark_shipped()` or `order.mark_delivered()` based on the requested status. Both methods update `_status` and stamp `_updated_at`.
5. **Persist order** — Call `await order_repo.save(order)`.
6. **In-app notification** — If `order.user_id` is not None, create a `NotificationEntity` with:
   - For `SHIPPED`: `_type=NotificationType.ORDER_SHIPPED`, `_subject="Your Order Has Shipped"`, `_body=f"Good news! Your order #{order.id[:8].upper()} is on its way."`.
   - For `DELIVERED`: `_type=NotificationType.ORDER_DELIVERED`, `_subject="Order Delivered"`, `_body=f"Your order #{order.id[:8].upper()} has been delivered. Enjoy your books!"`.
   - Set `_status=NotificationStatus.PENDING`, then call `await notification_repo.save(notification)`.
7. **Commit** — `await self._db_session.commit()`.
8. **Return** — Build and return `UpdateOrderStatusResult(id=order.id, status=order.status, updated_at=order.updated_at)`.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                              |
| -------------------- | ------ | ------------------------------------------------------------------ |
| `OrderEntity`        | Write  | `mark_shipped()` or `mark_delivered()` advances the status         |
| `NotificationEntity` | Write  | In-app notification created for the order owner on each transition |

### Repository Methods Required

| Interface                 | Method                 | New?          |
| ------------------------- | ---------------------- | ------------- |
| `IOrderRepository`        | `find_by_id(order_id)` | No (existing) |
| `IOrderRepository`        | `save(order)`          | No (existing) |
| `INotificationRepository` | `save(notification)`   | No (existing) |

### New DTOs

| DTO Class                  | Type            | Fields                                                   |
| -------------------------- | --------------- | -------------------------------------------------------- |
| `UpdateOrderStatusCommand` | Command (input) | `order_id: str`, `status: OrderStatus`                   |
| `UpdateOrderStatusResult`  | Result (output) | `id: str`, `status: OrderStatus`, `updated_at: datetime` |

### New Domain Exceptions

| Exception Class                     | File                             | Inherits          |
| ----------------------------------- | -------------------------------- | ----------------- |
| `OrderStatusTransitionInvalidError` | `app/domain/exceptions/order.py` | `DomainException` |

### New Error Codes

| Constant                          | Value                               | Description                                                   |
| --------------------------------- | ----------------------------------- | ------------------------------------------------------------- |
| `ORDER_STATUS_TRANSITION_INVALID` | `"ORDER_STATUS_TRANSITION_INVALID"` | Requested status transition is not allowed from current state |

### New `NotificationType` Values

| Constant          | Value               |
| ----------------- | ------------------- |
| `ORDER_SHIPPED`   | `"order_shipped"`   |
| `ORDER_DELIVERED` | `"order_delivered"` |

Add both to the `NotificationType` `StrEnum` in `app/core/constants.py`.

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/order/update_order_status/`

**`01_success_shipped.bru` — Happy Path (PAID → SHIPPED):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"shipped"`
- [x] `res.body.data.updated_at` is a valid ISO timestamp
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when `order_id` does not exist → `ORDER_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_order_status.py`

**Happy Path:**

- [x] `UpdateOrderStatusUseCase.execute(command_shipped)` returns `UpdateOrderStatusResult` with `status == OrderStatus.SHIPPED` when order is PAID
- [x] `UpdateOrderStatusUseCase.execute(command_delivered)` returns `UpdateOrderStatusResult` with `status == OrderStatus.DELIVERED` when order is SHIPPED

**Error Cases:**

- [x] Raises `OrderNotFoundError` when `order_repo.find_by_id` returns `None`
- [x] Raises `OrderStatusTransitionInvalidError` when attempting `SHIPPED` on a PENDING order
- [x] Raises `OrderStatusTransitionInvalidError` when attempting `SHIPPED` on a SHIPPED order (already advanced)
- [x] Raises `OrderStatusTransitionInvalidError` when attempting `DELIVERED` on a PAID order (skipping SHIPPED)
- [x] Raises `OrderStatusTransitionInvalidError` when attempting any transition on a CANCELLED order

**Edge Cases:**

- [x] In-app notification is saved with `NotificationType.ORDER_SHIPPED` when status advances to SHIPPED
- [x] In-app notification is saved with `NotificationType.ORDER_DELIVERED` when status advances to DELIVERED
- [x] No notification is attempted when `order.user_id` is None (user was deleted)

---

## Implementation Checklist

- [x] 1. Domain entity — _no changes needed (`mark_shipped`, `mark_delivered` already exist)_
- [x] 2. Domain exceptions (`app/domain/exceptions/order.py`) — _new: `OrderStatusTransitionInvalidError`; export in `__init__.py`_
- [x] 3. Repository interface methods — _all existing_
- [x] 4. DTOs (`app/application/dtos/order_dto.py`) — _new: `UpdateOrderStatusCommand`, `UpdateOrderStatusResult`_
- [x] 5. Constants (`app/core/constants.py`) — _add `NotificationType.ORDER_SHIPPED`, `NotificationType.ORDER_DELIVERED`_
- [x] 6. Use case (`app/application/use_cases/order/update_order_status.py`) — _new: `UpdateOrderStatusUseCase`_
- [x] 7. ORM model — _no change needed_
- [x] 8. Mapper — _no change needed_
- [x] 9. Repository implementation — _no change needed_
- [x] 10. Exception mapping (`app/presentation/http/exception_mapper.py`) — _add `OrderStatusTransitionInvalidError` → 409, `ORDER_STATUS_TRANSITION_INVALID`_
- [x] 11. Error codes (`app/application/errors/error_codes.py`) — _add `ORDER_STATUS_TRANSITION_INVALID`_
- [x] 12. Pydantic schemas (`app/presentation/schemas/order_schema.py`) — _new: `UpdateOrderStatusRequest`, `UpdateOrderStatusResponse`_
- [x] 13. Route handler (`app/presentation/api/app_api/v1/order_routes.py`) — _add `PATCH /{order_id}/status` handler_
- [x] 14. Wire in `deps.py` — _`AdminUser`, `OrderRepo`, `NotificationRepo` already wired_
- [x] 15. Alembic migration — _not needed (no schema change)_
- [x] 16. Bruno test files (`bruno/order/update_order_status/` — `folder.bru` + 2 test files)
- [x] 17. Pytest unit tests (`backend/tests/unit/test_update_order_status.py`)
