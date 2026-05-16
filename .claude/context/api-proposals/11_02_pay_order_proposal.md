# Order API Set — Pay Order Proposal

## Overview

| Field        | Value        |
| ------------ | ------------ |
| API Set      | 11. Order    |
| Use Case     | 2. Pay Order |
| File Index   | 11_02        |
| Access Level | 👤 Customer  |
| Status       | Implemented  |

---

## Endpoint

| Field  | Value                                   |
| ------ | --------------------------------------- |
| Method | POST                                    |
| URL    | `/api/app/v1/orders/{order_id}/payment` |
| Auth   | Bearer token (USER role)                |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter  | Type          | Description            |
| ---------- | ------------- | ---------------------- |
| `order_id` | string (UUID) | ID of the order to pay |

### Query Parameters

_(None)_

### Request Body

The body is a **discriminated union** on `payment_method`. Pydantic selects the correct schema automatically.

#### Online Banking

| Field            | Type                         | Required | Constraints             |
| ---------------- | ---------------------------- | -------- | ----------------------- |
| `payment_method` | `"online_banking"` (literal) | Yes      | Discriminator field     |
| `outcome`        | `"success"` \| `"failure"`   | Yes      | Simulation control only |
| `bank_name`      | string                       | Yes      | Non-empty               |
| `account_number` | string                       | Yes      | Non-empty               |

**Example:**

```json
{
  "payment_method": "online_banking",
  "outcome": "success",
  "bank_name": "Maybank",
  "account_number": "1234567890"
}
```

#### Card

| Field            | Type                       | Required | Constraints             |
| ---------------- | -------------------------- | -------- | ----------------------- |
| `payment_method` | `"card"` (literal)         | Yes      | Discriminator field     |
| `outcome`        | `"success"` \| `"failure"` | Yes      | Simulation control only |
| `card_number`    | string                     | Yes      | Non-empty               |
| `expiry_date`    | string                     | Yes      | Format: `MM/YYYY`       |
| `cvv`            | string                     | Yes      | Non-empty               |

**Example:**

```json
{
  "payment_method": "card",
  "outcome": "success",
  "card_number": "4111111111111111",
  "expiry_date": "08/2027",
  "cvv": "123"
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
    "order_id": "01932abc-1111-7000-aaaa-000000000001",
    "order_status": "paid",
    "payment": {
      "id": "01932abc-2222-7000-bbbb-000000000002",
      "method": "online_banking",
      "amount": "89.90",
      "status": "success",
      "simulated_ref": "BANK-TXN-01932ABC",
      "created_at": "2026-01-15T10:30:00Z"
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

> When `outcome` is `"failure"`, `order_status` is `"cancelled"`, `payment.status` is `"failed"`, and `payment.simulated_ref` is `null`.

### Error Responses

| HTTP Status | Error Code             | Condition                                                              |
| ----------- | ---------------------- | ---------------------------------------------------------------------- |
| 401         | `UNAUTHORIZED`         | No Authorization header provided                                       |
| 401         | `TOKEN_EXPIRED`        | Bearer token has expired                                               |
| 401         | `INVALID_TOKEN`        | Bearer token is malformed or revoked                                   |
| 404         | `ORDER_NOT_FOUND`      | Order does not exist, or belongs to a different user                   |
| 400         | `ORDER_NOT_PAYABLE`    | Order status is not `PENDING` (already paid, cancelled, etc.)          |
| 422         | `UNPROCESSABLE_ENTITY` | Pydantic validation failure (unknown `payment_method`, missing fields) |

---

## Procedures

1. Validate Bearer token via `CurrentUser` dependency. Returns active `UserEntity`. Handled by `deps.py`.

2. Pydantic validates the discriminated union request body using `payment_method` as the discriminator. Unknown `payment_method` values or missing method-specific fields return HTTP 422 automatically.

3. Fetch the order: `await order_repo.find_by_id(cmd.order_id)`. If `None`, raise `OrderNotFoundError(cmd.order_id)`.

4. Authorization guard: if `order.user_id != cmd.user_id`, raise `OrderNotFoundError(cmd.order_id)`. Treats unauthorised access as not-found to prevent order ID enumeration.

5. State guard: if `order.status != OrderStatus.PENDING`, raise `OrderNotPayableError(cmd.order_id, order.status)`.

6. Build `ProcessPaymentCommand` from the command: `order_id=order.id`, `amount=order.total`, `payment_method`, `outcome`, and the relevant method-specific details object (`OnlineBankingDetails` or `CardDetails`).

7. Call `await payment_service.process_payment(process_cmd)`. Internally, `PaymentServiceImpl` reads `process_cmd.payment_method` and instantiates the correct concrete strategy (`OnlineBankingPaymentStrategy` or `CardPaymentStrategy`) with the method-specific details, then delegates to `await strategy.process_payment(order_id, amount, outcome)`. Returns `PaymentProcessResult(success, method, simulated_ref)`.

8. Create a new `PaymentEntity`: `_id=str(uuid7())`, `_order_id=order.id`, `_method=result.method`, `_amount=order.total`, `_status=PaymentStatus.PENDING`, `_simulated_ref=None`.

9. **If `result.success` is `True`:**
   - Call `payment.mark_success(result.simulated_ref)` → sets `_status=PaymentStatus.SUCCESS` and stores `_simulated_ref`.
   - Call `order.mark_paid()` → sets `_status=OrderStatus.PAID` and updates `_updated_at`.
   - Create a `NotificationEntity` (`_id=str(uuid7())`, `_user_id=cmd.user_id`, `_type="payment_success"`, `_subject="Payment Confirmed"`, `_body` containing order reference and total, `_status=NotificationStatus.PENDING`, `_sent_at=None`) and call `await notification_repo.save(notification)`.

10. **If `result.success` is `False`:**
    - Call `payment.mark_failed()` → sets `_status=PaymentStatus.FAILED`.
    - Call `order.cancel()` → sets `_status=OrderStatus.CANCELLED` and updates `_updated_at`.
    - For each `item` in `order.order_items`: fetch `book = await book_repo.find_by_id(item.book_id)`. Call `book.increase_stock(item.quantity)`. Call `await book_repo.save(book)`. This restores the inventory reserved at order placement.

11. `await payment_repo.save(payment)`.

12. `await order_repo.save(order)`.

13. `await self._db_session.commit()`.

14. **After commit — on success only:** Call `email_notification_service.send_payment_receipt(...)` (Celery fire-and-forget). Pass `to=cmd.user_email`, `full_name=cmd.user_full_name`, `order_id`, `payment_ref=result.simulated_ref`, `payment_method_display`, `items` (mapped from `order.order_items` to `PaymentReceiptItem` list), `subtotal`, `shipping_cost`, `total`, `address_snapshot`, and `paid_at`.

15. Return `PayOrderResult(order_id=order.id, order_status=order.status, payment=PaymentSummaryResult(...))`.

---

## Domain Impact

### Entities Involved

| Entity          | Access       | Notes                                                         |
| --------------- | ------------ | ------------------------------------------------------------- |
| `OrderEntity`   | Read / Write | Status transitions: `PENDING → PAID` or `PENDING → CANCELLED` |
| `PaymentEntity` | Write        | New record created per payment attempt                        |
| `BookEntity`    | Read / Write | `increase_stock()` called per item on payment failure         |

### Repository Methods Required

| Interface            | Method                                                | New?                |
| -------------------- | ----------------------------------------------------- | ------------------- |
| `IOrderRepository`   | `find_by_id(order_id: str) -> OrderEntity \| None`    | Yes                 |
| `IOrderRepository`   | `save(order: OrderEntity) -> None`                    | No (existing)       |
| `IPaymentRepository` | `save(payment: PaymentEntity) -> None`                | Yes (new interface) |
| `IBookRepository`    | `find_by_id(book_id: str, ...) -> BookEntity \| None` | No (existing)       |
| `IBookRepository`    | `save(book: BookEntity) -> None`                      | No (existing)       |

### Entity Method Required

| Entity       | Method                                  | New? |
| ------------ | --------------------------------------- | ---- |
| `BookEntity` | `increase_stock(quantity: int) -> None` | Yes  |

### New Interfaces

| Interface                 | File                                                 | Purpose                                                   |
| ------------------------- | ---------------------------------------------------- | --------------------------------------------------------- |
| `IPaymentStrategy`        | `app/application/interfaces/payment_strategy.py`     | Abstract strategy; all concrete strategies implement this |
| `IPaymentService`         | `app/application/interfaces/payment_service.py`      | Port for the payment context; use case depends on this    |
| `INotificationRepository` | `app/domain/repositories/notification_repository.py` | Persists in-app `NotificationEntity` records              |

### New DTOs

| DTO Class               | Type             | Fields                                                                                                                                             |
| ----------------------- | ---------------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `OnlineBankingDetails`  | Input detail     | `bank_name: str`, `account_number: str`                                                                                                            |
| `CardDetails`           | Input detail     | `card_number: str`, `expiry_date: str`, `cvv: str`                                                                                                 |
| `PayOrderCommand`       | Command (input)  | `order_id`, `user_id`, `user_email: str`, `user_full_name: str`, `payment_method: str`, `outcome: str`, `online_banking_details?`, `card_details?` |
| `ProcessPaymentCommand` | Internal command | `order_id`, `amount: Decimal`, `payment_method: str`, `outcome: str`, `online_banking_details?`, `card_details?`                                   |
| `PaymentProcessResult`  | Strategy result  | `success: bool`, `method: str`, `simulated_ref: str`                                                                                               |
| `PaymentReceiptItem`    | Email helper     | `book_title: str`, `quantity: int`, `unit_price: Decimal`, `line_total: Decimal`                                                                   |
| `PaymentSummaryResult`  | Nested result    | `id`, `method`, `amount`, `status: PaymentStatus`, `simulated_ref?`, `created_at`                                                                  |
| `PayOrderResult`        | Result (output)  | `order_id`, `order_status: OrderStatus`, `payment: PaymentSummaryResult`                                                                           |

### New Domain Exceptions

| Exception Class        | File                             | Inherits          |
| ---------------------- | -------------------------------- | ----------------- |
| `OrderNotPayableError` | `app/domain/exceptions/order.py` | `DomainException` |

### New Error Codes

| Constant            | Value                 | Description                                      |
| ------------------- | --------------------- | ------------------------------------------------ |
| `ORDER_NOT_PAYABLE` | `"ORDER_NOT_PAYABLE"` | Order is not in PENDING state and cannot be paid |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/11_order/02_pay_order/`

Each test case is a separate `.bru` file.

**`01_success_online_banking.bru` — Happy Path (Online Banking):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.order_status` equals `"paid"`
- [x] `res.body.data.payment.status` equals `"success"`
- [x] `res.body.data.payment.method` equals `"online_banking"`
- [x] `res.body.data.payment.simulated_ref` starts with `"BANK-TXN-"`
- [x] `res.body.meta.requestId` is a string

**`02_success_card.bru` — Happy Path (Card):**

- [x] Status 200 OK
- [x] `res.body.data.order_status` equals `"paid"`
- [x] `res.body.data.payment.method` equals `"card"`
- [x] `res.body.data.payment.simulated_ref` starts with `"CARD-AUTH-"`

**`03_failure_online_banking.bru` — Simulated Failure:**

- [x] Status 200 OK
- [x] `res.body.data.order_status` equals `"cancelled"`
- [x] `res.body.data.payment.status` equals `"failed"`
- [x] `res.body.data.payment.simulated_ref` is `null`

**`04_order_not_found.bru` — Non-existent order ID:**

- [x] Status 404 → error code `ORDER_NOT_FOUND`

**`05_other_users_order.bru` — Order belongs to different user:**

- [x] Status 404 → error code `ORDER_NOT_FOUND`

**`06_order_not_payable.bru` — Order already paid:**

- [x] Status 400 → error code `ORDER_NOT_PAYABLE`

**`07_invalid_payment_method.bru` — Unknown `payment_method` value:**

- [x] Status 422

### Pytest Unit Tests

**File:** `backend/tests/unit/test_pay_order.py`

**Happy Path:**

- [x] `PayOrderUseCase.execute(valid_online_banking_command)` returns `PayOrderResult` with `order_status=PAID`, `payment.status=PaymentStatus.SUCCESS`
- [x] `PayOrderUseCase.execute(valid_card_command)` returns `PayOrderResult` with `order_status=PAID`, `payment.status=PaymentStatus.SUCCESS`

**Failure Simulation:**

- [x] `execute(command_with_outcome_failure)` returns `PayOrderResult` with `order_status=CANCELLED`, `payment.status=PaymentStatus.FAILED`, `payment.simulated_ref=None`
- [x] After failure, book stock is restored by `item.quantity` for each order item

**Error Cases:**

- [x] Raises `OrderNotFoundError` when order does not exist
- [x] Raises `OrderNotFoundError` when `order.user_id != command.user_id`
- [x] Raises `OrderNotPayableError` when `order.status == OrderStatus.PAID`
- [x] Raises `OrderNotPayableError` when `order.status == OrderStatus.CANCELLED`

---

## Implementation Checklist

- [x] 1. `app/core/constants.py` — add `PaymentMethod(StrEnum)` with `ONLINE_BANKING = "online_banking"` and `CARD = "card"` values
- [x] 2. `app/domain/entities/book_entity.py` — add `increase_stock(quantity: int) -> None` method
- [x] 3. `app/domain/exceptions/order.py` — add `OrderNotPayableError`; export from `app/domain/exceptions/__init__.py`
- [x] 4. `app/domain/repositories/order_repository.py` — add `find_by_id(order_id: str) -> OrderEntity | None` abstract method
- [x] 5. `app/domain/repositories/payment_repository.py` — new `IPaymentRepository` with `save(payment: PaymentEntity) -> None`; export from `app/domain/repositories/__init__.py`
- [x] 6. `app/application/interfaces/payment_strategy.py` — new `IPaymentStrategy` ABC with `async process_payment(order_id, amount, outcome) -> PaymentProcessResult`; include `PaymentProcessResult` dataclass
- [x] 7. `app/application/interfaces/payment_service.py` — new `IPaymentService` ABC with `async process_payment(command: ProcessPaymentCommand) -> PaymentProcessResult`
- [x] 8. `app/application/dtos/payment_dto.py` — new DTOs: `OnlineBankingDetails`, `CardDetails`, `PayOrderCommand`, `ProcessPaymentCommand`, `PaymentSummaryResult`, `PayOrderResult`
- [x] 9. `app/application/use_cases/order/pay_order.py` — new `PayOrderUseCase`
- [x] 10. `app/application/errors/error_codes.py` — add `ORDER_NOT_PAYABLE = "ORDER_NOT_PAYABLE"`
- [x] 11. `app/infrastructure/payment/strategies/online_banking_strategy.py` — `OnlineBankingPaymentStrategy(IPaymentStrategy)`; simulated ref format: `BANK-TXN-{order_id[:8].upper()}`
- [x] 12. `app/infrastructure/payment/strategies/card_strategy.py` — `CardPaymentStrategy(IPaymentStrategy)`; simulated ref format: `CARD-AUTH-{order_id[:8].upper()}`
- [x] 13. `app/infrastructure/payment/payment_service_impl.py` — `PaymentServiceImpl(IPaymentService)`; selects strategy from `ProcessPaymentCommand.payment_method`; no strategy selection in `deps.py`
- [x] 14. `app/infrastructure/db/repositories/payment_repository_impl.py` — `PaymentRepositoryImpl(IPaymentRepository)`
- [x] 15. `app/infrastructure/db/repositories/order_repository_impl.py` — implement `find_by_id()`; load `OrderItemEntity` and `PaymentEntity` via `selectin`
- [x] 16. `app/presentation/http/exception_mapper.py` — map `OrderNotPayableError` → HTTP 400, `ORDER_NOT_PAYABLE`
- [x] 17. `app/presentation/schemas/order_schema.py` — add `OnlineBankingPaymentRequest`, `CardPaymentRequest`, `PayOrderRequest` (discriminated union), `PaymentSummaryResponse`, `PayOrderResponse`
- [x] 18. `app/presentation/api/app_api/v1/order_routes.py` — add `POST /orders/{order_id}/payment` route handler
- [x] 19. `app/presentation/dependencies/deps.py` — add `PaymentRepo`, `PaymentSvc`, and `NotificationRepo` typed aliases
- [x] 20. Alembic migration — no migration needed; `payments` and `notifications` tables already exist
- [x] 21. `app/domain/repositories/notification_repository.py` — new `INotificationRepository` with `save(notification: NotificationEntity) -> None`; export from `app/domain/repositories/__init__.py`
- [x] 22. `app/infrastructure/db/repositories/notification_repository_impl.py` — `NotificationRepositoryImpl(INotificationRepository)`
- [x] 23. `app/application/interfaces/email_notification_service.py` — add `send_payment_receipt(...)` abstract method
- [x] 24. `app/infrastructure/tasks/email_notification_service.py` — implement `send_payment_receipt()` with full HTML payment receipt
- [x] 25. `bruno/order/02_pay_order/` — `folder.bru` + 7 test files (no unauthorized/no-header tests)
- [x] 26. `backend/tests/unit/test_pay_order.py` — unit tests

---

## Integration Note — Migrating to a Real Payment Provider

This section describes what changes when a real payment provider (e.g. Billplz, Stripe, FPX) replaces the simulation. The Strategy Pattern was introduced precisely to make this migration additive rather than destructive.

### What stays the same

- `IPaymentStrategy` interface — the contract is unchanged; only the concrete strategies are replaced
- `IPaymentService` interface and `PaymentServiceImpl` — the context class survives; only the strategies it selects are swapped
- `PayOrderUseCase` — depends only on `IPaymentService`; no changes required
- `PaymentEntity`, `IPaymentRepository`, all DTOs — unchanged

### What changes or gets added

**1. Replace concrete strategies with real provider adapters**

Each concrete strategy (`OnlineBankingPaymentStrategy`, `CardPaymentStrategy`) becomes an HTTP adapter that calls the provider's API (e.g. via `httpx`). They still implement `IPaymentStrategy` but their `process_payment` bodies replace the simulation with real API calls.

**2. Remove the `outcome` field**

The `outcome: "success" | "failure"` field is simulation scaffolding only. Remove it from `PayOrderRequest`, `PayOrderCommand`, `ProcessPaymentCommand`, and the `IPaymentStrategy.process_payment` signature. Concrete strategies determine the real outcome from the provider's response.

**3. Introduce an async payment flow (if the provider requires it)**

Most providers are asynchronous: your server initiates a payment session, receives a redirect URL, and later gets notified via webhook. This requires two new use cases:

- **Initiate Payment** — calls the provider, returns a redirect URL; the current Pay Order use case is retired or repurposed
- **Payment Webhook Handler** — receives the provider's callback and updates `PaymentEntity` and `OrderEntity` status

**4. Add method-specific provider config**

Each provider strategy will need API keys and endpoint URLs. These belong in `app/core/config.py` (new provider config section) and are injected into the concrete strategy via `deps.py` at construction time.

**5. Re-evaluate retry**

With a real provider, a failed payment attempt does not automatically cancel the order — the customer should be able to retry with a different method. This requires a new **Retry Payment** use case. The current cancel-on-failure behaviour in `PayOrderUseCase` is not extended — it is retired when the real flow is introduced.
