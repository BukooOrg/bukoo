# Order API Set — Cancel Order Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 11. Order       |
| Use Case     | 5. Cancel Order |
| File Index   | 11_05           |
| Access Level | 👤🔑 Both       |
| Status       | Implemented     |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | POST                                    |
| URL    | `/api/app/v1/orders/{order_id}/cancel`  |
| Auth   | Bearer token (any role — USER or ADMIN) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter  | Type          | Description               |
| ---------- | ------------- | ------------------------- |
| `order_id` | string (UUID) | ID of the order to cancel |

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
    "status": "cancelled",
    "updated_at": "2026-01-15T10:45:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:45:01Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                                                                        |
| ----------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------- |
| 401         | `UNAUTHORIZED`          | No Authorization header provided                                                                                 |
| 401         | `TOKEN_EXPIRED`         | Bearer token is expired                                                                                          |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or invalid                                                                             |
| 403         | `ORDER_ACCESS_DENIED`   | Authenticated customer attempts to cancel another user's order                                                   |
| 404         | `ORDER_NOT_FOUND`       | No order exists for the given `order_id`                                                                         |
| 409         | `ORDER_NOT_CANCELLABLE` | Customer attempts to cancel a non-PENDING order, or admin attempts to cancel a SHIPPED/DELIVERED/CANCELLED order |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency validates the Bearer token, checks the blocklist, and returns the active `UserEntity`. Both `UserRole.USER` and `UserRole.ADMIN` are accepted.
2. **Fetch order** — Call `order_repo.find_by_id(order_id)`. If `None`, raise `OrderNotFoundError(order_id)`.
3. **Ownership check** — If `current_user.role == UserRole.USER` and `order.user_id != current_user.id`, raise `OrderAccessDeniedError(order_id)`.
4. **Cancellability check (Customer)** — If `current_user.role == UserRole.USER` and `order.status != OrderStatus.PENDING`, raise `OrderNotCancellableError(order_id, order.status)`.
5. **Cancellability check (Admin)** — If `current_user.role == UserRole.ADMIN` and `order.status not in (OrderStatus.PENDING, OrderStatus.PAID)`, raise `OrderNotCancellableError(order_id, order.status)`.
6. **Mutate order** — Call `order.cancel()`. This sets `order.status = OrderStatus.CANCELLED` and stamps `order._updated_at`.
7. **Restore stock** — For each `item` in `order.order_items`: if `item.book_id` is not None, call `book_repo.find_by_id(item.book_id, BookStatusFilter())`. If the book is found, call `book.increase_stock(item.quantity)` and `await book_repo.save(book)`. If the book is not found (deleted or deactivated), skip silently.
8. **Persist order** — Call `await order_repo.save(order)`.
9. **In-app notification** — If `order.user_id` is not None, look up the order owner via `user_repo.find_by_id(order.user_id)`. If found, create a `NotificationEntity` with `_type=NotificationType.ORDER_CANCELLED`, `_subject="Order Cancelled"`, `_body=f"Your order #{order.id[:8].upper()} has been cancelled. If you did not request this, please contact support."`, `_status=NotificationStatus.PENDING`, then call `await notification_repo.save(notification)`.
10. **Commit** — `await self._db_session.commit()`.
11. **Dispatch cancellation email** — After commit, call `email_notification_service.send_order_cancellation(to=owner.email, full_name=owner.full_name, order_id=order.id, items=[...], total=order.total)` (fire-and-forget; errors do not roll back the cancellation). Skip if the owner user was not found in step 9.
12. **Return** — Build and return `CancelOrderResult(id=order.id, status=order.status, updated_at=order.updated_at)`.

> **Refund note:** The existing `PaymentEntity` (if any) is left unchanged (`status = success`). Cancellation is recorded on the order status alone. The UI should infer "refund issued" from `order.status == CANCELLED` with `payment.status == success`.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                       |
| -------------------- | ------ | ----------------------------------------------------------- |
| `OrderEntity`        | Write  | `cancel()` transitions status to CANCELLED                  |
| `OrderItemEntity`    | Read   | Iterated to restore stock; accessed via `order.order_items` |
| `BookEntity`         | Write  | `increase_stock(qty)` called for each item's book           |
| `UserEntity`         | Read   | Order owner looked up to obtain email/name for notification |
| `NotificationEntity` | Write  | New in-app notification created for the order owner         |

### Repository Methods Required

| Interface                 | Method                                    | New?          |
| ------------------------- | ----------------------------------------- | ------------- |
| `IOrderRepository`        | `find_by_id(order_id)`                    | No (existing) |
| `IOrderRepository`        | `save(order)`                             | No (existing) |
| `IBookRepository`         | `find_by_id(book_id, BookStatusFilter())` | No (existing) |
| `IBookRepository`         | `save(book)`                              | No (existing) |
| `IUserRepository`         | `find_by_id(user_id)`                     | No (existing) |
| `INotificationRepository` | `save(notification)`                      | No (existing) |

### New DTOs

| DTO Class            | Type            | Fields                                                   |
| -------------------- | --------------- | -------------------------------------------------------- |
| `CancelOrderCommand` | Command (input) | `order_id: str`, `user_id: str`, `user_role: UserRole`   |
| `CancelOrderResult`  | Result (output) | `id: str`, `status: OrderStatus`, `updated_at: datetime` |

### New Service Interface Method

`IEmailNotificationService` gains one new abstract method:

```python
@abstractmethod
def send_order_cancellation(
    self,
    to: str,
    full_name: str,
    order_id: str,
    items: list[PaymentReceiptItem],
    total: Decimal,
    cancelled_at: datetime,
) -> None:
    pass
```

> `PaymentReceiptItem` (already defined in `payment_dto.py`) is reused here — it carries `book_title`, `quantity`, `unit_price`, and `line_total`, which are all available from `OrderItemEntity`.

### New Domain Exceptions

| Exception Class            | File                             | Inherits          |
| -------------------------- | -------------------------------- | ----------------- |
| `OrderNotCancellableError` | `app/domain/exceptions/order.py` | `DomainException` |

> `OrderAccessDeniedError` was introduced in proposal 11.4 and is referenced here as an existing exception.

### New Error Codes

| Constant                | Value                     | Description                                                           |
| ----------------------- | ------------------------- | --------------------------------------------------------------------- |
| `ORDER_NOT_CANCELLABLE` | `"ORDER_NOT_CANCELLABLE"` | Order is in a status that does not permit cancellation by this caller |

### New `NotificationType` Value

| Constant          | Value               |
| ----------------- | ------------------- |
| `ORDER_CANCELLED` | `"order_cancelled"` |

Add to the `NotificationType` `StrEnum` in `app/core/constants.py`.

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/order/cancel_order/`

**`01_success_customer.bru` — Happy Path (customer cancels own PENDING order):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"cancelled"`
- [x] `res.body.data.updated_at` is a valid ISO timestamp
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when `order_id` does not exist → `ORDER_NOT_FOUND`
- [x] `03_access_denied.bru` — Status 403 when customer requests cancellation of another user's order → `ORDER_ACCESS_DENIED`
- [x] `04_not_cancellable_customer.bru` — Status 409 when customer attempts to cancel a PAID order → `ORDER_NOT_CANCELLABLE`
- [x] `05_not_cancellable_admin.bru` — Status 409 when admin attempts to cancel a SHIPPED order → `ORDER_NOT_CANCELLABLE`
- [x] `06_success_admin_paid.bru` — Status 200 when admin cancels a PAID order belonging to another user

### Pytest Unit Tests

**File:** `backend/tests/unit/test_cancel_order.py`

**Happy Path:**

- [x] `CancelOrderUseCase.execute(customer_command)` returns `CancelOrderResult` with `status == OrderStatus.CANCELLED` when customer owns a PENDING order
- [x] `CancelOrderUseCase.execute(admin_command)` returns `CancelOrderResult` with `status == OrderStatus.CANCELLED` when admin cancels a PAID order belonging to another user

**Error Cases:**

- [x] Raises `OrderNotFoundError` when `order_repo.find_by_id` returns `None`
- [x] Raises `OrderAccessDeniedError` when `user_role == UserRole.USER` and `order.user_id != command.user_id`
- [x] Raises `OrderNotCancellableError` when customer attempts to cancel a PAID order
- [x] Raises `OrderNotCancellableError` when customer attempts to cancel a SHIPPED order
- [x] Raises `OrderNotCancellableError` when admin attempts to cancel a SHIPPED order
- [x] Raises `OrderNotCancellableError` when admin attempts to cancel an already CANCELLED order

**Edge Cases:**

- [x] Stock is restored for all items when a PENDING order is cancelled — `book.increase_stock()` called once per item
- [x] Items with `book_id == None` (book was deleted) are skipped during stock restoration without raising an exception
- [x] In-app notification is created and saved when `order.user_id` is not None
- [x] No notification is attempted when `order.user_id` is None (user was deleted)

---

## Implementation Checklist

- [x] 1. Domain entity — _no changes needed_
- [x] 2. Domain exceptions (`app/domain/exceptions/order.py`) — _new: `OrderNotCancellableError`; export in `__init__.py`_
- [x] 3. Repository interface methods — _all existing_
- [x] 4. DTOs (`app/application/dtos/order_dto.py`) — _new: `CancelOrderCommand`, `CancelOrderResult`_
- [x] 5. Service interface (`app/application/interfaces/email_notification_service.py`) — _add `send_order_cancellation` abstract method_
- [x] 6. Constants (`app/core/constants.py`) — _add `NotificationType.ORDER_CANCELLED`_
- [x] 7. Use case (`app/application/use_cases/order/cancel_order.py`) — _new: `CancelOrderUseCase`_
- [x] 8. ORM model — _no change needed_
- [x] 9. Mapper — _no change needed_
- [x] 10. Repository implementation — _no change needed_
- [x] 11. Email service implementation — _implement `send_order_cancellation` in the concrete email service_
- [x] 12. Exception mapping (`app/presentation/http/exception_mapper.py`) — _add `OrderNotCancellableError` → 409, `ORDER_NOT_CANCELLABLE`_
- [x] 13. Error codes (`app/application/errors/error_codes.py`) — _add `ORDER_NOT_CANCELLABLE`_
- [x] 14. Pydantic schemas (`app/presentation/schemas/order_schema.py`) — _new: `CancelOrderResponse`_
- [x] 15. Route handler (`app/presentation/api/app_api/v1/order_routes.py`) — _add `POST /{order_id}/cancel` handler_
- [x] 16. Wire in `deps.py` — _add `UserRepo` typed alias if not already present; `OrderRepo`, `BookRepo`, `NotificationRepo`, `EmailNotificationService` already wired_
- [x] 17. Alembic migration — _not needed (no schema change)_
- [x] 18. Bruno test files (`bruno/order/04_cancel_order/` — `folder.bru` + 6 test files)
- [x] 19. Pytest unit tests (`backend/tests/unit/test_cancel_order.py`)
