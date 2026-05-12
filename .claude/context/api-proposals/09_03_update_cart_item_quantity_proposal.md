# Cart API — Update Cart Item Quantity Proposal

## Overview

| Field        | Value                        |
| ------------ | ---------------------------- |
| API Set      | 9. Cart                      |
| Use Case     | 3. Update Cart Item Quantity |
| File Index   | 09_03                        |
| Access Level | 👤 Customer                  |
| Status       | Implemented                  |

---

## Endpoint

| Field  | Value                              |
| ------ | ---------------------------------- |
| Method | PATCH                              |
| URL    | `/api/app/v1/cart/items/{item_id}` |
| Auth   | Bearer token (USER role)           |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                    |
| --------- | ------------- | ------------------------------ |
| item_id   | string (UUID) | The cart item ID to be updated |

### Query Parameters

_(None)_

### Request Body

| Field    | Type    | Required | Constraints |
| -------- | ------- | -------- | ----------- |
| quantity | integer | Yes      | Must be ≥ 1 |

**Example:**

```json
{
  "quantity": 3
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
    "id": "019612ab-...",
    "cart_id": "01961298-...",
    "book_id": "01961201-...",
    "quantity": 3,
    "book": {
      "id": "01961201-...",
      "title": "The Pragmatic Programmer",
      "price": "39.99",
      "cover_url": "https://..."
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                             |
| ----------- | -------------------- | ----------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No Authorization header or token is expired / invalid |
| 404         | CART_NOT_FOUND       | No cart exists for the authenticated user             |
| 404         | CART_ITEM_NOT_FOUND  | `item_id` does not exist in the user's cart           |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (e.g. `quantity` < 1)     |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and returns the active `UserEntity`. FastAPI raises HTTP 401 automatically on failure.

2. **Input validation** — FastAPI/Pydantic validates the request body. `quantity` must be an integer ≥ 1; Pydantic returns HTTP 422 automatically if this fails.

3. **Load cart** — `UpdateCartItemQuantityUseCase.execute(cmd)` calls `await self._cart_repo.find_by_user_id(cmd.user_id)`. If `None` is returned, raise `CartNotFoundError`.

4. **Load cart item** — Call `cart.find_item_by_cart_item_id(cmd.item_id)`. If `None` is returned, raise `CartItemNotFoundError(cmd.item_id)`. Item existence is guaranteed beyond this point.

5. **Update quantity** — Call `cart.update_item_quantity(cmd.item_id, cmd.quantity)`. This method finds the item by `item_id`, calls `item.change_quantity(qty)`, and updates `cart._updated_at`. No `ValueError` risk since item existence was confirmed in step 4.

6. **Persist** — Call `await self._cart_repo.save(cart)`. The repository does not commit.

7. **Commit** — Call `await self._db_session.commit()`.

8. **Return** — Retrieve the updated item with `cart.find_item_by_cart_item_id(cmd.item_id)`, build and return `UpdateCartItemQuantityResult` with the item's current `id`, `cart_id`, `book_id`, `quantity`, and nested `CartItemBookResult` from `item.book`.

---

## Domain Impact

### Entities Involved

| Entity           | Access       | Notes                                                                                                                                             |
| ---------------- | ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CartEntity`     | Read / Write | Rename `find_item(book_id)` → `find_item_by_book_id(book_id)`; add `find_item_by_cart_item_id(item_id)`; add `update_item_quantity(item_id, qty)` |
| `CartItemEntity` | Read / Write | Existing `change_quantity(qty)` called internally by `update_item_quantity`                                                                       |

### Repository Methods Required

| Interface         | Method                     | New?          |
| ----------------- | -------------------------- | ------------- |
| `ICartRepository` | `find_by_user_id(user_id)` | No (existing) |
| `ICartRepository` | `save(cart)`               | No (existing) |

### New DTOs

| DTO Class                       | Type            | Fields                                                                                 |
| ------------------------------- | --------------- | -------------------------------------------------------------------------------------- |
| `UpdateCartItemQuantityCommand` | Command (input) | `item_id: str`, `quantity: int`, `user_id: str`                                        |
| `UpdateCartItemQuantityResult`  | Result (output) | `id: str`, `cart_id: str`, `book_id: str`, `quantity: int`, `book: CartItemBookResult` |

`CartItemBookResult` already exists in `cart_dtos.py` — reuse it.

### New Domain Exceptions

| Exception Class         | File                            | Inherits          |
| ----------------------- | ------------------------------- | ----------------- |
| `CartNotFoundError`     | `app/domain/exceptions/cart.py` | `DomainException` |
| `CartItemNotFoundError` | `app/domain/exceptions/cart.py` | `DomainException` |

### New Error Codes

| Constant              | Value                   | Description                               |
| --------------------- | ----------------------- | ----------------------------------------- |
| `CART_NOT_FOUND`      | `"CART_NOT_FOUND"`      | No cart exists for the authenticated user |
| `CART_ITEM_NOT_FOUND` | `"CART_ITEM_NOT_FOUND"` | No cart item found for the given ID       |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/09 Cart/03 Update Cart Item Quantity/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.quantity` equals the submitted value (e.g. 3)
- [x] `res.body.data.id` matches the path parameter `item_id`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_cart_not_found.bru` — Status 404 when the user has no cart → error code `CART_NOT_FOUND`
- [x] `03_item_not_found.bru` — Status 404 when `item_id` does not exist in the user's cart → error code `CART_ITEM_NOT_FOUND`
- [x] `04_invalid_quantity.bru` — Status 422 when `quantity` is 0 or negative

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_cart_item_quantity.py`

**Happy Path:**

- [x] `UpdateCartItemQuantityUseCase.execute(valid_command)` returns `UpdateCartItemQuantityResult` with updated `quantity` and correct `book` data

**Error Cases:**

- [x] Raises `CartNotFoundError` when `cart_repo.find_by_user_id` returns `None`
- [x] Raises `CartItemNotFoundError` when the cart exists but `item_id` is not in the cart items list

**Edge Cases:**

- [x] Setting quantity to 1 (minimum boundary) succeeds

---

## Implementation Checklist

- [x] 1. Domain entity — rename `find_item` → `find_item_by_book_id`; add `find_item_by_cart_item_id(item_id)`; add `update_item_quantity(item_id, qty)` in `app/domain/entities/cart_entity.py` (also update `add_cart_item.py` call site for the rename)
- [x] 2. Domain exceptions — create `app/domain/exceptions/cart.py` with `CartNotFoundError` and `CartItemNotFoundError`; export both from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface methods — no new methods needed
- [x] 4. DTOs — add `UpdateCartItemQuantityCommand` and `UpdateCartItemQuantityResult` to `app/application/dtos/cart_dtos.py`
- [x] 5. Use case — `app/application/use_cases/cart/update_cart_item_quantity.py`
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — no new methods needed
- [x] 9. Exception mapping — add `CartNotFoundError` and `CartItemNotFoundError` to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `CART_NOT_FOUND` and `CART_ITEM_NOT_FOUND` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `UpdateCartItemQuantityRequest` and `UpdateCartItemQuantityResponse` to `app/presentation/schemas/cart_schema.py`
- [x] 12. Route handler — add `PATCH /cart/items/{item_id}` to `app/presentation/api/app_api/v1/cart_routes.py`
- [x] 13. Wire in `deps.py` — no new dependencies needed (reuses `CartRepo`, `DbSession`, `CurrentUser`)
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files — `folder.bru` + 6 `.bru` files under `bruno/09 Cart/03 Update Cart Item Quantity/`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_update_cart_item_quantity.py`
