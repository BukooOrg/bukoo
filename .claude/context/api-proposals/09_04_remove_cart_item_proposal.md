# Cart API Set — Remove Cart Item Proposal

## Overview

| Field        | Value               |
| ------------ | ------------------- |
| API Set      | 9. Cart             |
| Use Case     | 4. Remove Cart Item |
| File Index   | 09_04               |
| Access Level | 👤 Customer         |
| Status       | Implemented         |

---

## Endpoint

| Field  | Value                              |
| ------ | ---------------------------------- |
| Method | DELETE                             |
| URL    | `/api/app/v1/cart/items/{item_id}` |
| Auth   | Bearer token (USER role)           |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                   |
| --------- | ------------- | ----------------------------- |
| item_id   | string (UUID) | ID of the cart item to remove |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 204 No Content

_(Empty body — the middleware envelope is not emitted for 204 responses)_

### Error Responses

| HTTP Status | Error Code           | Condition                                           |
| ----------- | -------------------- | --------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | No Authorization header or token is invalid/expired |
| 404         | CART_NOT_FOUND       | The authenticated user has no active cart           |
| 404         | CART_ITEM_NOT_FOUND  | `item_id` does not exist in the user's cart         |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (malformed UUID)        |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and returns the active `UserEntity`. Raises HTTP 401 if invalid or expired.

2. **Fetch cart** — Call `cart_repo.find_by_user_id(current_user.id)`. If the result is `None`, raise `CartNotFoundError(current_user.id)` → mapped to HTTP 404 / `CART_NOT_FOUND`.

3. **Verify item belongs to cart** — Call `cart.find_item_by_cart_item_id(cmd.item_id)`. If `None`, raise `CartItemNotFoundError(cmd.item_id)` → mapped to HTTP 404 / `CART_ITEM_NOT_FOUND`. This prevents one user from deleting another user's cart items.

4. **Remove item** — Call `cart.remove_item(item.book_id)`. `CartEntity.remove_item` filters the item from `_cart_items` and updates `_updated_at`.

5. **Persist** — Call `await cart_repo.save(cart)`. The repository does not commit.

6. **Commit** — Call `await self._db_session.commit()` in the use case.

7. **Return** — Return `RemoveCartItemResult()` (empty marker DTO). The route handler returns HTTP 204 with no body.

---

## Domain Impact

### Entities Involved

| Entity           | Access | Notes                                        |
| ---------------- | ------ | -------------------------------------------- |
| `CartEntity`     | Write  | `remove_item(book_id)` mutates `_cart_items` |
| `CartItemEntity` | Read   | Used to verify ownership; removed from cart  |

### Repository Methods Required

| Interface         | Method                | New?          |
| ----------------- | --------------------- | ------------- |
| `ICartRepository` | `find_by_user_id(id)` | No (existing) |
| `ICartRepository` | `save(cart)`          | No (existing) |

### New DTOs

| DTO Class               | Type            | Fields                           |
| ----------------------- | --------------- | -------------------------------- |
| `RemoveCartItemCommand` | Command (input) | `item_id: str`, `user_id: str`   |
| `RemoveCartItemResult`  | Result (output) | _(empty — signals success only)_ |

### New Domain Exceptions

_(None — `CartNotFoundError` and `CartItemNotFoundError` already exist in `app/domain/exceptions/cart.py`)_

### New Error Codes

_(None — `CART_NOT_FOUND` and `CART_ITEM_NOT_FOUND` already exist in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/09_cart/04_remove_cart_item/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 204 No Content
- [x] Response body is empty

**Error Cases:**

- [x] `02_item_not_found.bru` — Status 404 when `item_id` does not exist in the user's cart → error code `CART_ITEM_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_remove_cart_item.py`

**Happy Path:**

- [x] `RemoveCartItemUseCase.execute(valid_command)` returns `RemoveCartItemResult` and the item is gone from the cart

**Error Cases:**

- [x] Raises `CartNotFoundError` when `cart_repo.find_by_user_id` returns `None`
- [x] Raises `CartItemNotFoundError` when `item_id` is not in the user's cart

**Edge Cases:**

- [x] Item from a different user's cart cannot be removed (item lookup against the current user's cart returns `None`)

---

## Implementation Checklist

- [x] 1. Domain entity — no changes needed
- [x] 2. Domain exceptions — no changes needed (`CartNotFoundError`, `CartItemNotFoundError` exist)
- [x] 3. Repository interface methods — no changes needed (`find_by_user_id`, `save` exist)
- [x] 4. DTOs — add `RemoveCartItemCommand` and `RemoveCartItemResult` to `app/application/dtos/cart_dtos.py`
- [x] 5. Use case — `app/application/use_cases/cart/remove_cart_item.py` (`RemoveCartItemUseCase`)
- [x] 6. ORM model — no changes needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation — no changes needed
- [x] 9. Exception mapping — no changes needed (`CartItemNotFoundError` already mapped)
- [x] 10. Error codes — no changes needed
- [x] 11. Pydantic schemas — no new request schema needed; no response schema needed (204)
- [x] 12. Route handler — add `DELETE /items/{item_id}` to `app/presentation/api/app_api/v1/cart_routes.py`
- [x] 13. Wire in `deps.py` — no changes needed (`CartRepo`, `CustomerUser`, `DbSession` exist)
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/09_cart/04_remove_cart_item/` (`folder.bru` + `01_success.bru` + error cases)
- [x] 16. Pytest unit tests — `backend/tests/unit/test_remove_cart_item.py`
