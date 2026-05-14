# Order API Set — Place Order Proposal

## Overview

| Field        | Value          |
| ------------ | -------------- |
| API Set      | 11. Order      |
| Use Case     | 1. Place Order |
| File Index   | 11_01          |
| Access Level | 👤 Customer    |
| Status       | Implemented    |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | POST                     |
| URL    | `/api/app/v1/orders`     |
| Auth   | Bearer token (USER role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

_(None)_

### Request Body

| Field         | Type            | Required | Constraints                                  |
| ------------- | --------------- | -------- | -------------------------------------------- |
| cart_item_ids | array of string | Yes      | Min 1 item; each must be a valid UUID string |

**Example:**

```json
{
  "cart_item_ids": [
    "019255ab-0000-7000-8000-000000000001",
    "019255ab-0000-7000-8000-000000000003"
x]
}
```

---

## Response

### Success Response

**Status:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "019255ab-0000-7000-8000-000000000010",
    "status": "pending",
    "subtotal": "109.94",
    "shipping_cost": "5.00",
    "total": "114.94",
    "address_snapshot": {
      "recipient_name": "John Doe",
      "phone": "+60123456789",
      "address_line1": "No. 1, Jalan Bukit Bintang",
      "address_line2": null,
      "city": "Kuala Lumpur",
      "state": "Wilayah Persekutuan Kuala Lumpur",
      "postcode": "55100",
      "country": "Malaysia"
    },
    "items": [
      {
        "id": "019255ac-0000-7000-8000-000000000011",
        "book_id": "019245ab-0000-7000-8000-000000000003",
        "book_title": "The Great Gatsby",
        "unit_price": "54.97",
        "quantity": 2,
        "line_total": "109.94"
      }
  x],
    "created_at": "2026-05-13T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-13T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                                             |
| ----------- | -------------------- | ------------------------------------------------------------------------------------- |
| 401         | INVALID_TOKEN        | No Authorization header, or token is expired / invalid                                |
| 404         | CART_NOT_FOUND       | The authenticated user has no active cart                                             |
| 404         | CART_ITEM_NOT_FOUND  | A provided `cart_item_id` does not exist in the user's cart                           |
| 404         | ADDRESS_NOT_FOUND    | The user has no saved shipping address; they must add one via `PUT /users/me/address` |
| 404         | BOOK_NOT_FOUND       | A selected cart item references a book that is deleted or deactivated                 |
| 409         | OUT_OF_STOCK         | A selected book has insufficient stock for the requested quantity                     |
| 422         | UNPROCESSABLE_ENTITY | `cart_item_ids` is missing or is an empty array (Pydantic, before use case runs)      |

---

## Procedures

1. **Auth guard.** The `CurrentUser` dependency validates the Bearer token, checks the blocklist, and confirms the user is active. The route handler extracts `current_user.id` and passes it into `PlaceOrderCommand`.

2. **Input validation.** FastAPI/Pydantic validates the request body. The `cart_item_ids` field requires `min_length=1` — an empty array `[]` or a missing field is rejected with 422 before the use case is reached.

3. **Load the cart.** The use case calls `await cart_repo.find_by_user_id(command.user_id)`. If `None`, raise `CartNotFoundError(command.user_id)` → 404 `CART_NOT_FOUND`.

4. **Resolve selected cart items.** For each `cart_item_id` in `command.cart_item_ids`, call `cart.find_item_by_cart_item_id(cart_item_id)`. If `None` (the ID does not belong to this user's cart), raise `CartItemNotFoundError(cart_item_id)` → 404 `CART_ITEM_NOT_FOUND`. Collect the resolved `CartItemEntity` objects into a `selected_items` list.

5. **Load the shipping address.** Call `await address_repo.find_by_user_id(command.user_id)`. If `None`, raise `AddressNotFoundError(command.user_id)` → 404 `ADDRESS_NOT_FOUND`.

6. **Compute shipping cost.** Inspect `address.state.strip().lower()`:
   - Equals `"sabah"` or `"sarawak"`: `shipping_cost = Decimal("10.00")` (East Malaysia rate).
   - Anything else: `shipping_cost = Decimal("5.00")` (Peninsular Malaysia rate).

7. **Validate books and stock — read-only pass, no mutations yet.** For each `cart_item` in `selected_items`:
   - Call `await book_repo.find_by_id(cart_item.book_id, BookStatusFilter(status="activate"))`. If `None`, raise `BookNotFoundError(cart_item.book_id)` → 404 `BOOK_NOT_FOUND`.
   - If `book.stock_quantity < cart_item.quantity`, raise `OutOfStockError(book.id, cart_item.quantity, book.stock_quantity)` → 409 `OUT_OF_STOCK`.
   - Collect each validated `(cart_item, book)` pair into a list for the mutation phase.

8. **Snapshot the shipping address.** Call `address_snapshot = address.to_snapshot()`, which returns a plain `dict` with keys: `recipient_name`, `phone`, `address_line1`, `address_line2`, `city`, `state`, `postcode`, `country`.

9. **Construct the `OrderEntity`.** Create a new `OrderEntity` with:
   - `_id = str(uuid7())`
   - `_user_id = command.user_id`
   - `_address_snapshot = address_snapshot`
   - `_subtotal = Decimal("0")` (recalculated incrementally below)
   - `_shipping_cost = shipping_cost`
   - `_total = shipping_cost` (starts as shipping cost alone, grows with each item addition)
   - `_status = OrderStatus.PENDING`
   - `_created_at = _updated_at = datetime.now(UTC)`

10. **Build and attach `OrderItemEntity` records.** For each `(cart_item, book)` pair from Step 7:
    - Create `OrderItemEntity` with: `_id=str(uuid7())`, `_order_id=order.id`, `_book_id=book.id`, `_book_title=book.title`, `_unit_price=book.price`, `_quantity=cart_item.quantity`, `_line_total=book.price * cart_item.quantity`, `_created_at=_updated_at=datetime.now(UTC)`.
    - Call `order.add_order_item(order_item)`, which appends the item and calls `_calculate_totals()` to recompute `_subtotal` and `_total`.

11. **Decrease stock for each selected book.** For each `(cart_item, book)` pair, call `book.decrease_stock(cart_item.quantity)`.

12. **Persist mutated books.** For each modified book, call `await book_repo.save(book, should_skip_book_authors=True)`. The repository does not commit.

13. **Persist the order.** Call `await order_repo.save(order)`. The repository persists the `OrderModel` and all nested `OrderItemModel` records as a single aggregate write. The repository does not commit.

14. **Remove only the ordered cart items.** For each `cart_item` in `selected_items`, call `await cart_repo.delete_item_by_item_id(cart_item.id)`. Unselected cart items are left untouched. The repository does not commit.

15. **Commit the transaction.** Call `await self._db_session.commit()`. This single commit atomically persists the new order, all stock decrements, and the removal of the selected cart items.

16. **Return the result.** Build and return `PlaceOrderResult` from the committed `order` entity, including a `PlaceOrderItemResult` for each item in `order.order_items`.

---

## Domain Impact

### Entities Involved

| Entity            | Access | Notes                                                                        |
| ----------------- | ------ | ---------------------------------------------------------------------------- |
| `CartEntity`      | Read   | Source of item resolution; only selected items are removed after order       |
| `CartItemEntity`  | Read   | Provides `book_id` and `quantity` for each selected line item                |
| `AddressEntity`   | Read   | Provides shipping address snapshot and state for cost calculation            |
| `BookEntity`      | Write  | `decrease_stock()` called per selected item; `title` and `price` snapshotted |
| `OrderEntity`     | Write  | Created new with `OrderStatus.PENDING`                                       |
| `OrderItemEntity` | Write  | One per selected cart item; carries the price snapshot                       |

### Repository Methods Required

| Interface            | Method                                                   | New?                    |
| -------------------- | -------------------------------------------------------- | ----------------------- |
| `ICartRepository`    | `find_by_user_id(user_id: str)`                          | No (existing)           |
| `ICartRepository`    | `delete_item_by_item_id(item_id: str)`                   | No (existing)           |
| `IAddressRepository` | `find_by_user_id(user_id: str) -> AddressEntity \| None` | **Yes (new method)**    |
| `IBookRepository`    | `find_by_id(book_id, BookStatusFilter)`                  | No (existing)           |
| `IBookRepository`    | `save(book, should_skip_book_authors=True)`              | No (existing)           |
| `IOrderRepository`   | `save(order: OrderEntity) -> None`                       | **Yes (new interface)** |

### New DTOs

**File:** `app/application/dtos/order_dtos.py`

| DTO Class              | Type            | Fields                                                                                                                                                                                             |
| ---------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `PlaceOrderCommand`    | Command (input) | `user_id: str`, `cart_item_ids: list[str]`                                                                                                                                                         |
| `PlaceOrderItemResult` | Result (output) | `id: str`, `book_id: str \| None`, `book_title: str`, `unit_price: Decimal`, `quantity: int`, `line_total: Decimal`                                                                                |
| `PlaceOrderResult`     | Result (output) | `id: str`, `status: OrderStatus`, `subtotal: Decimal`, `shipping_cost: Decimal`, `total: Decimal`, `address_snapshot: dict[str, Any]`, `items: list[PlaceOrderItemResult]`, `created_at: datetime` |

### New Domain Exceptions

_(None — `CartNotFoundError`, `CartItemNotFoundError`, `AddressNotFoundError`, `BookNotFoundError`, and `OutOfStockError` all already exist and are mapped.)_

### New Error Codes

_(None — all required error codes already exist in `ErrorCode`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/order/01_place_order/`

**`01_success.bru` — Happy Path (Peninsular Malaysia, partial cart selection):**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.status` equals `"pending"`
- [x] `res.body.data.shipping_cost` equals `"5.00"`
- [x] `res.body.data.total` equals `subtotal + 5.00`
- [x] `res.body.data.items` contains only the selected cart items (not all cart items)
- [x] `res.body.data.address_snapshot` contains the user's profile address fields
- [x] `res.body.meta.requestId` is a string

**`02_success_east_malaysia.bru` — Happy Path (East Malaysia address):**

- [x] Status 201 Created
- [x] `res.body.data.shipping_cost` equals `"10.00"`
- [x] `res.body.data.address_snapshot.state` is `"Sabah"` or `"Sarawak"`

**`03_empty_cart_item_ids.bru` — Status 422 when `cart_item_ids` is an empty array `[]`**

**`04_cart_not_found.bru` — Status 404 → `CART_NOT_FOUND` when user has no cart**

**`05_cart_item_not_found.bru` — Status 404 → `CART_ITEM_NOT_FOUND` when a provided ID is not in the user's cart**

**`06_address_not_found.bru` — Status 404 → `ADDRESS_NOT_FOUND` when user has no saved address**

**`07_book_not_found.bru` — Status 404 → `BOOK_NOT_FOUND` when a selected item's book is deleted or deactivated**

**`08_out_of_stock.bru` — Status 409 → `OUT_OF_STOCK` when a selected item exceeds available stock**

### Pytest Unit Tests

**File:** `backend/tests/unit/test_place_order.py`

**Happy Path:**

- [x] `PlaceOrderUseCase.execute(valid_command)` returns `PlaceOrderResult` with `status == OrderStatus.PENDING`
- [x] `PlaceOrderResult.items` contains only the items whose IDs were in `cart_item_ids`; unselected items are excluded
- [x] `PlaceOrderResult.shipping_cost` equals `Decimal("5.00")` when address state is `"Selangor"`
- [x] `PlaceOrderResult.shipping_cost` equals `Decimal("10.00")` when address state is `"Sabah"`
- [x] `PlaceOrderResult.shipping_cost` equals `Decimal("10.00")` when address state is `"Sarawak"`
- [x] `PlaceOrderResult.total` equals `subtotal + shipping_cost`
- [x] `PlaceOrderResult.items` carries correct `book_title` and `unit_price` snapshots
- [x] `cart_repo.delete_item_by_item_id` is called once per selected item; unselected items are not deleted
- [x] `book_repo.save` is called once per selected item (stock decremented)

**Error Cases:**

- [x] Raises `CartNotFoundError` when `cart_repo.find_by_user_id` returns `None`
- [x] Raises `CartItemNotFoundError` when a provided `cart_item_id` is not found in the cart
- [x] Raises `AddressNotFoundError` when `address_repo.find_by_user_id` returns `None`
- [x] Raises `BookNotFoundError` when a selected item's book is not found or deactivated
- [x] Raises `OutOfStockError` when a selected book's `stock_quantity` is less than the cart item quantity

**Edge Cases:**

- [x] Shipping cost is `Decimal("10.00")` when address state is `"sabah"` (lowercase — case-insensitive match)
- [x] Shipping cost is `Decimal("10.00")` when address state is `"SARAWAK"` (uppercase — case-insensitive match)
- [x] Order with multiple selected items correctly accumulates `subtotal` across all `add_order_item` calls
- [x] No mutations occur if any validation fails — all stock checks run before any `decrease_stock` call
- [x] A cart item ID that belongs to a different user's cart is rejected with `CartItemNotFoundError` (implicitly, since it won't appear in the loaded cart)

---

## Implementation Checklist

- [x] 1. Domain entity — `OrderEntity`, `OrderItemEntity` — **existing**
- [x] 2. Domain exceptions — all required exceptions — **existing**
- [x] 3. Repository interfaces:
  - [x] `IOrderRepository` — `app/domain/repositories/order_repository.py`
  - [x] `IAddressRepository.find_address_by_user_id()` — new method on existing interface (named `find_address_by_user_id` in impl)
- [x] 4. DTOs — `PlaceOrderCommand`, `BaseOrderItemResult`, `PlaceOrderResult` — `app/application/dtos/order_dto.py`
- [x] 5. Use case — `app/application/use_cases/order/place_order.py`
- [x] 6. ORM model — `OrderModel`, `OrderItemModel` — **existing**
- [x] 7. Mapper — `OrderMapper`, `OrderItemMapper` — **existing**
- [x] 8. Repository implementations:
  - [x] `OrderRepositoryImpl.save()` — `app/infrastructure/db/repositories/order_repository_impl.py`
  - [x] `AddressRepositoryImpl.find_address_by_user_id()` — new method on existing impl
- [x] 9. Exception mapping — all exceptions already in `EXCEPTION_MAP` — **no changes needed**
- [x] 10. Error codes — all codes already in `ErrorCode` — **no changes needed**
- [x] 11. Pydantic schemas — `app/presentation/schemas/order_schema.py`; `cart_item_ids` uses `Field(min_length=1)`
- [x] 12. Route handler — `app/presentation/api/app_api/v1/order_routes.py`; registered in `v1/__init__.py`
- [x] 13. Wire in `deps.py` — `OrderRepo`, `AddressRepo`, `CustomerUser` all wired
- [x] 14. Alembic migration — **not needed** (`orders` and `order_items` tables already exist)
- [x] 15. Bruno test files — `bruno/order/01_place_order/` — `folder.bru` + `01_success.bru` through `10_out_of_stock.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_place_order.py`
