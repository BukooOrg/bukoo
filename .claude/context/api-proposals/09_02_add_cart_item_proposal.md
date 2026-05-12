# Cart API Set — Add Cart Item Proposal

## Overview

| Field        | Value            |
| ------------ | ---------------- |
| API Set      | 9. Cart          |
| Use Case     | 2. Add Cart Item |
| File Index   | 09_02            |
| Access Level | 👤 Customer      |
| Status       | Implemented      |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | POST                     |
| URL    | `/api/app/v1/cart/items` |
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

| Field      | Type    | Required | Constraints            |
| ---------- | ------- | -------- | ---------------------- |
| `book_id`  | string  | Yes      | Valid UUID of the book |
| `quantity` | integer | Yes      | `>= 1`                 |

**Example:**

```json
{
  "book_id": "01932abc-0001-7000-a000-000000000001",
  "quantity": 2
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
    "id": "01932abc-0002-7000-b000-000000000001",
    "cartId": "01932abc-0003-7000-c000-000000000001",
    "bookId": "01932abc-0001-7000-a000-000000000001",
    "quantity": 2,
    "book": {
      "id": "01932abc-0001-7000-a000-000000000001",
      "title": "The Name of the Wind",
      "price": "29.99",
      "coverUrl": "books/cover/01932abc.jpg"
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

When the book is already in the cart, `quantity` reflects the **new total** after incrementing (e.g. had 1, added 2 → `"quantity": 3`).

### Error Responses

| HTTP Status | Error Code         | Condition                                                 |
| ----------- | ------------------ | --------------------------------------------------------- |
| 401         | `UNAUTHORIZED`     | No Authorization header                                   |
| 401         | `TOKEN_EXPIRED`    | Token is expired                                          |
| 401         | `INVALID_TOKEN`    | Token is malformed or revoked                             |
| 404         | `BOOK_NOT_FOUND`   | `book_id` does not exist, is soft-deleted, or deactivated |
| 409         | `OUT_OF_STOCK`     | `book.stock_quantity < 1`                                 |
| 422         | `VALIDATION_ERROR` | Pydantic validation failure (e.g. `quantity < 1`)         |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and returns the authenticated `UserEntity`. If invalid, returns 401 before reaching the use case.

2. **Input validation** — FastAPI/Pydantic validates the request body: `book_id` must be a non-empty string and `quantity` must be an integer `>= 1`. Returns 422 automatically on failure.

3. **Fetch the book** — Call `IBookRepository.find_by_id(command.book_id, BookStatusFilter(status="activate"))`. This returns `None` if the book does not exist, is soft-deleted, or is deactivated. If `None`, raise `BookNotFoundError(command.book_id)`.

4. **Stock check** — If `book.stock_quantity < 1`, raise `OutOfStockError(command.book_id)`.

5. **Fetch or create the cart** — Call `ICartRepository.find_by_user_id(current_user.id)`. If `None` (first-time user), construct a new `CartEntity(_id=str(uuid7()), _user_id=current_user.id, _created_at=datetime.now(UTC), _updated_at=datetime.now(UTC), _cart_items=[])`.

6. **Add item to cart** — Check if the book is already in the cart by inspecting `cart.cart_items` for a matching `book_id`:
   - **Duplicate:** Call `cart.add_item(book, command.quantity)`, which calls `existing_item.increase_quantity(command.quantity)` and updates `cart._updated_at`.
   - **New item:** Construct a new `CartItemEntity(_id=str(uuid7()), _cart_id=cart.id, _book_id=book.id, _quantity=command.quantity, _created_at=datetime.now(UTC), _updated_at=datetime.now(UTC), _book=book)`. Then call `cart.append_item(new_item)` — a new domain method that appends the pre-built entity to `cart._cart_items` and updates `cart._updated_at`.

7. **Persist** — Call `await cart_repo.save(cart)`. The repository merges the `CartModel` and upserts each `CartItemModel` in `cart.cart_items`. Repo does NOT commit.

8. **Commit** — `await self._db_session.commit()`.

9. **Return** — Retrieve the final `CartItemEntity` from `cart.cart_items` where `book_id == command.book_id`. Build and return `AddCartItemResult` containing the item fields plus the nested book summary.

---

## Domain Impact

### Entities Involved

| Entity           | Access       | Notes                                                 |
| ---------------- | ------------ | ----------------------------------------------------- |
| `CartEntity`     | Read / Write | Auto-created if no cart exists for the user           |
| `CartItemEntity` | Read / Write | New line created, or existing line quantity increased |
| `BookEntity`     | Read         | Validated for existence, activation state, and stock  |

### Repository Methods Required

| Interface         | Method                                                | New?                |
| ----------------- | ----------------------------------------------------- | ------------------- |
| `IBookRepository` | `find_by_id(book_id, filters)`                        | No (existing)       |
| `ICartRepository` | `find_by_user_id(user_id: str) -> CartEntity \| None` | Yes — new interface |
| `ICartRepository` | `save(cart: CartEntity) -> None`                      | Yes — new interface |

### New Entity Method Required

`CartEntity.append_item(item: CartItemEntity) -> None` — appends a pre-built `CartItemEntity` to `_cart_items` and updates `_updated_at`. This is required because `add_item()` only handles the duplicate (increment) path; the comment in that method explicitly states the service layer must construct and pass the entity.

### New DTOs

| DTO Class            | Type            | Fields                                                                                 |
| -------------------- | --------------- | -------------------------------------------------------------------------------------- |
| `AddCartItemCommand` | Command (input) | `book_id: str`, `quantity: int`                                                        |
| `AddCartItemResult`  | Result (output) | `id: str`, `cart_id: str`, `book_id: str`, `quantity: int`, `book: CartItemBookResult` |
| `CartItemBookResult` | Nested result   | `id: str`, `title: str`, `price: Decimal`, `cover_url: str \| None`                    |

### New Domain Exceptions

_(None — `BookNotFoundError` and `OutOfStockError` are reused from existing `book.py` and `order.py` exception groups respectively.)_

### New Error Codes

_(None — `BOOK_NOT_FOUND` and `OUT_OF_STOCK` already exist in `ErrorCode`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/09_cart/02_add_cart_item/`

**`01_success_new_item.bru` — Happy Path (new book added):**

- [ ] Status 201 Created
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.quantity` equals the requested quantity
- [ ] `res.body.data.book.id` matches the requested `book_id`
- [ ] `res.body.meta.requestId` is a string

**`02_success_duplicate.bru` — Happy Path (duplicate book, quantity incremented):**

- [ ] Status 201 Created
- [ ] `res.body.data.quantity` equals the sum of prior quantity + requested quantity

**Error Cases:**

- [ ] `03_book_not_found.bru` — Status 404 when `book_id` does not exist → error code `BOOK_NOT_FOUND`
- [ ] `04_book_deactivated.bru` — Status 404 when book is deactivated → error code `BOOK_NOT_FOUND`
- [ ] `05_out_of_stock.bru` — Status 409 when book has `stock_quantity == 0` → error code `OUT_OF_STOCK`
- [ ] `06_invalid_quantity.bru` — Status 422 when `quantity < 1` → error code `VALIDATION_ERROR`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_add_cart_item.py`

**Happy Path:**

- [ ] `AddCartItemUseCase.execute(valid_command)` with no existing cart returns `AddCartItemResult` with `quantity == command.quantity`
- [ ] `AddCartItemUseCase.execute(valid_command)` with existing cart and duplicate book returns `AddCartItemResult` with `quantity == existing_quantity + command.quantity`

**Error Cases:**

- [ ] Raises `BookNotFoundError` when book repo returns `None`
- [ ] Raises `OutOfStockError` when `book.stock_quantity == 0`

**Edge Cases:**

- [ ] Cart is auto-created (persisted via `cart_repo.save`) when user has no existing cart
- [ ] Adding to an existing cart with multiple items only modifies the targeted book's line item

---

## Implementation Checklist

- [x] 1. Domain entity — update `CartEntity.append_item(item: CartItemEntity) -> None` (`app/domain/entities/cart_entity.py`)
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface — create `ICartRepository` (`app/domain/repositories/cart_repository.py`) with `find_by_user_id` and `save`
- [x] 4. DTOs — `AddCartItemCommand`, `AddCartItemResult`, `CartItemBookResult` (`app/application/dtos/cart_dtos.py`)
- [x] 5. Use case — `AddCartItemUseCase` (`app/application/use_cases/cart/add_cart_item.py`)
- [x] 6. ORM model — `CartModel`, `CartItemModel` (`app/infrastructure/db/models/cart_model.py`) — _already existed_
- [x] 7. Mapper — `CartMapper`, `CartItemMapper` (`app/infrastructure/db/mappers/cart_mapper.py`) — _already existed_
- [x] 8. Repository implementation — `CartRepositoryImpl` (`app/infrastructure/db/repositories/cart_repository_impl.py`)
- [x] 9. Exception mapping — no new entries (existing `BookNotFoundError` and `OutOfStockError` already mapped)
- [x] 10. Error codes — no new entries
- [x] 11. Pydantic schemas — `AddCartItemRequest`, `CartItemResponse` (`app/presentation/schemas/cart_schema.py`)
- [x] 12. Route handler — `POST /cart/items` in `app/presentation/api/app_api/v1/cart_routes.py`
- [x] 13. Wire in `deps.py` — `get_cart_repository()` provider and `CartRepo` typed alias
- [x] 14. Alembic migration — skipped; `carts` and `cart_items` tables already exist (migration `2026_04_29_0929`)
- [x] 15. Bruno test files — `bruno/09_cart/02_add_cart_item/` (folder.bru + 6 test files)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_add_cart_item.py`

---

### Architecture Decision Note

< 1 vs < cmd.quantity — Detailed Comparison

---

Approach A: book.stock_quantity < 1 (current)

Rejects only if the book is completely out of stock. A user can add any quantity to cart as long as at least 1 copy exists.

Pros

- Cart as wishlist: Matches a model where the cart is just intent, not a stock reservation. Users can "save" quantities they want even if supply is uncertain.
- Fewer false rejections: If 2 are in stock and a user adds 5, the cart accepts it. At checkout, the order use case enforces the real limit with precise, transactional stock checks.
- Simpler mental model for the cart layer: Cart never needs to worry about stock math — that belongs to order creation, where stock is actually decremented.
- Avoids TOCTOU races at cart stage: Stock can change between adding to cart and checking out anyway. Enforcing at cart time gives a false sense of precision.

Cons

- Deferred UX pain: The user only discovers the quantity problem at checkout — potentially after entering their address, payment info, etc.
- OutOfStockError.requested/available fields are useless: available is always 0 when this check fires, making the error's detail fields meaningless.
- Inconsistent with the error's intent: OutOfStockError was designed for order creation (where requested vs. available is a meaningful distinction). Reusing it here with a weaker check
  is semantically odd.

---

Approach B: book.stock_quantity < cmd.quantity (suggested)

Rejects if the book doesn't have enough stock to satisfy the requested quantity.

Pros

- Immediate, specific feedback: The user knows right away that they're asking for more than what's available. They can adjust the quantity before proceeding.
- Error fields are meaningful: OutOfStockError(requested=3, available=2) accurately describes the situation — the error was built for exactly this.
- Matches common e-commerce UX: Most storefronts (Amazon, Shopify) enforce stock limits at add-to-cart time, not just at checkout.
- Prevents obviously invalid cart states: Allowing a cart with qty=100 when stock=1 is noise. The cart reflects something the system knows can't be fulfilled.

Cons

- TOCTOU (Time-of-Check-Time-of-Use) gap: Stock can be purchased by another user between add-to-cart and checkout. Passing the cart check doesn't guarantee the order will succeed — you
  still need enforcement at order creation. So this check adds friction without eliminating the need for a downstream check.
- Over-restrictive for high-demand items: If stock fluctuates rapidly (flash sales), valid add-to-cart attempts get rejected even though the item might be restocked before checkout.
- Cart and order layers become coupled by stock logic: You're now duplicating stock enforcement across two use cases. If the rule changes (e.g., allow 10% over-stock for backorders), you
  need to update both places.

Summary Table

| Criterion                        | < 1                             | < cmd.quantity |
| -------------------------------- | ------------------------------- | -------------- |
| UX feedback speed                | Deferred to checkout            | Immediate      |
| Error detail accuracy            | Poor (available always 0)       | Accurate       |
| Handles TOCTOU correctly         | No (but neither does the other) | No             |
| Requires downstream check anyway | Yes                             | Yes            |
| Cart as wishlist semantics       | ✓                               | ✗              |
| Matches common storefront UX     | ✗                               | ✓              |
| Stock logic duplication          | Minimal                         | Yes            |

Bottom line: < cmd.quantity wins on UX and error accuracy. < 1 wins on architectural purity — it keeps the cart dumb and lets order creation own all stock enforcement. Neither eliminates
the need for a stock check at order creation time, so the real question is whether you want early feedback or a clean separation of concerns.

**Decision:** Use < 1
