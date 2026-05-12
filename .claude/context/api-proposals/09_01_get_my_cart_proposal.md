# Cart API Set — Get My Cart Proposal

## Overview

| Field        | Value          |
| ------------ | -------------- |
| API Set      | 9. Cart        |
| Use Case     | 1. Get My Cart |
| File Index   | 09_01          |
| Access Level | 👤 Customer    |
| Status       | Implemented    |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | GET                      |
| URL    | `/api/app/v1/cart`       |
| Auth   | Bearer token (USER role) |

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
    "id": "01932abc-0000-7000-0000-000000000001",
    "items": [
      {
        "id": "01932abc-0000-7000-0000-000000000003",
        "cartId": "01932abc-0000-7000-0000-000000000001",
        "bookId": "01932abc-0000-7000-0000-000000000004",
        "quantity": 2,
        "book": {
          "id": "01932abc-0000-7000-0000-000000000004",
          "title": "The Pragmatic Programmer",
          "price": "49.99",
          "coverUrl": "https://..."
        }
      }
  x]
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code         | Condition                                 |
| ----------- | ------------------ | ----------------------------------------- |
| 401         | AUTH_TOKEN_INVALID | Missing, expired, or revoked Bearer token |
| 404         | CART_NOT_FOUND     | No cart exists for the authenticated user |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency validates the Bearer token, checks the blocklist via `RedisCacheService`, and returns the active `UserEntity`. Handled entirely by `deps.py`; the use case never touches auth.

2. **Load cart** — Call `cart_repo.find_by_user_id(user.id)`. This returns a `CartEntity` with its `_cart_items` list already eagerly loaded (selectin). If the result is `None`, raise `CartNotFoundError(user_id=user.id)`.

3. **Return result** — Build and return a `GetMyCartResult` DTO from the `CartEntity`. For each `CartItemEntity` in `cart.cart_items`, build a `CartItemResult` containing the item fields and the nested `CartItemBookResult` (resolved from `item.book`). No `commit()` is called — this is a read-only operation.

---

## Domain Impact

### Entities Involved

| Entity           | Access | Notes                                        |
| ---------------- | ------ | -------------------------------------------- |
| `CartEntity`     | Read   | Loaded by user_id; contains cart_items       |
| `CartItemEntity` | Read   | Eagerly loaded via selectin on CartModel     |
| `BookEntity`     | Read   | Eagerly loaded via selectin on CartItemModel |

### Repository Methods Required

| Interface         | Method                          | New?          |
| ----------------- | ------------------------------- | ------------- |
| `ICartRepository` | `find_by_user_id(user_id: str)` | No (existing) |

### New DTOs

| DTO Class          | Type            | Fields                                                                                 |
| ------------------ | --------------- | -------------------------------------------------------------------------------------- |
| `GetMyCartCommand` | input           | `user_id: str`                                                                         |
| `GetMyCartResult`  | Result (output) | `id: str`, `user_id: str`, `items: list[CartItemResult]`                               |
| `CartItemResult`   | Result (output) | `id: str`, `cart_id: str`, `book_id: str`, `quantity: int`, `book: CartItemBookResult` |

> Note: `CartItemBookResult` already exists in `cart_dtos.py` — reuse it.

### New Domain Exceptions

_(None — `CartNotFoundError` already exists in `app/domain/exceptions/cart.py`)_

### New Error Codes

_(None — `CART_NOT_FOUND` error code to be confirmed; add if not already present in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/cart/get_my_cart/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a string
- [x] `res.body.data.items` is an array
- [x] Each item has `id`, `cartId`, `bookId`, `quantity`, and `book` fields
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_cart_not_found.bru` — Status 404 when authenticated user has no cart → error code `CART_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_my_cart.py`

**Happy Path:**

- [x] `GetMyCartUseCase.execute(valid_query)` returns `GetMyCartResult` with correct `id`, `user_id`, and populated `items` list
- [x] Returns `GetMyCartResult` with empty `items` list when cart has no items

**Error Cases:**

- [x] Raises `CartNotFoundError` when `cart_repo.find_by_user_id` returns `None`

---

## Implementation Checklist

- [x] 1. Domain entity — reuse existing `CartEntity` and `CartItemEntity`
- [x] 2. Domain exceptions — reuse existing `CartNotFoundError`
- [x] 3. Repository interface method — `find_by_user_id` already exists on `ICartRepository`
- [x] 4. DTOs — add `GetMyCartQuery`, `GetMyCartResult`, `CartItemResult` to `app/application/dtos/cart_dtos.py`
- [x] 5. Use case — `app/application/use_cases/cart/get_my_cart.py`
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — no new method needed
- [x] 9. Exception mapping — confirm `CartNotFoundError` → 404 `CART_NOT_FOUND` is in `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — confirm `CART_NOT_FOUND` exists in `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `GetMyCartResponse`, `CartItemResponse`, update `cart_schema.py`
- [x] 12. Route handler — add `GET /` handler to `app/presentation/api/app_api/v1/cart_routes.py`
- [x] 13. Wire in `deps.py` — `CartRepo` and `CustomerUser` already wired
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/09_cart/01_get_my_cart/` with `folder.bru` + `01_success.bru` + `02_cart_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_get_my_cart.py`
