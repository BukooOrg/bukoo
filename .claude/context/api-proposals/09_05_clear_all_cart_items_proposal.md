# Cart API Set — Clear All Cart Items Proposal

## Overview

| Field        | Value                   |
| ------------ | ----------------------- |
| API Set      | 9. Cart                 |
| Use Case     | 5. Clear All Cart Items |
| File Index   | 09_05                   |
| Access Level | 👤 Customer             |
| Status       | Implemented             |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | DELETE                   |
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
    "items": []
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

2. **Load cart** — Call `cart_repo.find_by_user_id(cmd.user_id)`. If the result is `None`, raise `CartNotFoundError(cmd.user_id)`. The returned `CartEntity` includes its `_cart_items` list eagerly loaded via selectin.

3. **Clear items** — Call `cart.clear()`. This sets `_cart_items = []` and updates `_updated_at` on the entity.

4. **Persist** — Call `cart_repo.save(cart)`. The repository does not commit.

5. **Commit** — Call `await self._db_session.commit()`.

6. **Return** — Build and return `ClearCartResult(id=cart.id)`.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                                               |
| ------------ | ------ | --------------------------------------------------- |
| `CartEntity` | Write  | `cart.clear()` removes all items, updates timestamp |

### Repository Methods Required

| Interface         | Method                          | New?          |
| ----------------- | ------------------------------- | ------------- |
| `ICartRepository` | `find_by_user_id(user_id: str)` | No (existing) |
| `ICartRepository` | `save(cart: CartEntity)`        | No (existing) |

### New DTOs

| DTO Class          | Type            | Fields         |
| ------------------ | --------------- | -------------- |
| `ClearCartCommand` | Command (input) | `user_id: str` |
| `ClearCartResult`  | Result (output) | `id: str`      |

### New Domain Exceptions

_(None — `CartNotFoundError` already exists in `app/domain/exceptions/cart.py`)_

### New Error Codes

_(None — `CART_NOT_FOUND` already exists in `app/application/errors/error_codes.py`)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/09_cart/05_clear_all_cart_items/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.data.items` is an empty array
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

_(None)_

### Pytest Unit Tests

**File:** `backend/tests/unit/test_clear_all_cart_items.py`

**Happy Path:**

- [x] `ClearAllCartItemsUseCase.execute(valid_command)` returns `ClearCartResult` with correct `id`
- [x] Cart with multiple items is fully cleared (items list becomes empty after execution)

**Error Cases:**

- [x] Raises `CartNotFoundError` when `cart_repo.find_by_user_id` returns `None`

**Edge Cases:**

- [x] Clearing an already-empty cart succeeds without error

---

## Implementation Checklist

- [x] 1. Domain entity — reuse existing `CartEntity` (`clear()` already implemented)
- [x] 2. Domain exceptions — reuse existing `CartNotFoundError`
- [x] 3. Repository interface methods — `find_by_user_id` and `save` already exist on `ICartRepository`
- [x] 4. DTOs — add `ClearAllCartItemsCommand`, `ClearAllCartItemsResult` to `app/application/dtos/cart_dtos.py`
- [x] 5. Use case — `app/application/use_cases/cart/clear_all_cart_items.py`
- [x] 6. ORM model — no new table needed
- [x] 7. Mapper — no new mapper needed
- [x] 8. Repository implementation — no new method needed
- [x] 9. Exception mapping — `CartNotFoundError` → 404 `CART_NOT_FOUND` already mapped
- [x] 10. Error codes — `CART_NOT_FOUND` already exists
- [x] 11. Pydantic schemas — add `ClearAllCartItemsResponse` to `app/presentation/schemas/cart_schema.py`
- [x] 12. Route handler — add `DELETE /` handler to `app/presentation/api/app_api/v1/cart_routes.py`
- [x] 13. Wire in `deps.py` — `CartRepo` and `CustomerUser` already wired
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `bruno/cart/05_clear_all_cart_items/` with `folder.bru` + `01_success.bru` + `02_no_auth.bru` + `03_cart_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_clear_all_cart_items.py`
