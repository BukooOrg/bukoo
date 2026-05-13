# Wishlist API Set — Move Wishlist Item to Cart Proposal

## Overview

| Field        | Value                         |
| ------------ | ----------------------------- |
| API Set      | 10. Wishlist                  |
| Use Case     | 4. Move Wishlist Item to Cart |
| File Index   | 10_04                         |
| Access Level | 👤 Customer                   |
| Status       | Implemented                   |

---

## Endpoint

| Field  | Value                                               |
| ------ | --------------------------------------------------- |
| Method | POST                                                |
| URL    | `/api/app/v1/wishlist/items/{item_id}/move-to-cart` |
| Auth   | Bearer token (USER role)                            |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                     |
| --------- | ------------- | ------------------------------- |
| item_id   | string (UUID) | ID of the wishlist item to move |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 201 Created

```json
{
  "success": true,
  "data": {
    "id": "01932abc-0000-7000-a000-000000000020",
    "cart_id": "01932abc-0000-7000-a000-000000000005",
    "book_id": "01932abc-0000-7000-a000-000000000001",
    "quantity": 1,
    "book": {
      "id": "01932abc-0000-7000-a000-000000000001",
      "title": "The Name of the Wind",
      "price": "29.99",
      "cover_url": "http://localhost:9000/covers/name-of-the-wind.jpg"
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-13T08:00:00Z"
  }
}
```

> If the book was already in the cart, the existing cart item's quantity is incremented by 1, and that cart item's data is returned.

### Error Responses

| HTTP Status | Error Code                | Condition                                                      |
| ----------- | ------------------------- | -------------------------------------------------------------- |
| 404         | `WISHLIST_NOT_FOUND`      | The authenticated user has no wishlist                         |
| 404         | `WISHLIST_ITEM_NOT_FOUND` | `item_id` does not exist in the user's wishlist                |
| 404         | `BOOK_NOT_FOUND`          | The book linked to the wishlist item is deactivated or deleted |
| 409         | `OUT_OF_STOCK`            | The book's `stock_quantity` is 0                               |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency decodes the Bearer token, checks the blocklist, and returns the active `UserEntity`. HTTP 401 is raised by `deps.py` on failure; not handled by the use case.

2. **Wishlist resolution** — Call `await self._wishlist_repo.find_by_user_id(cmd.user_id)`. If `None`, raise `WishlistNotFoundError(cmd.user_id)`, which maps to HTTP 404 `WISHLIST_NOT_FOUND`.

3. **Item lookup** — Iterate `wishlist.wishlist_items` and find the item whose `id == cmd.wishlist_item_id`. If not found, raise `WishlistItemNotFoundError(cmd.wishlist_item_id)`, which maps to HTTP 404 `WISHLIST_ITEM_NOT_FOUND`.

4. **Book validation** — Call `await self._book_repo.find_by_id(item.book_id, BookStatusFilter(status="activate"))`. If `None` (book deleted or deactivated since being wishlisted), raise `BookNotFoundError(item.book_id)`, which maps to HTTP 404 `BOOK_NOT_FOUND`.

5. **Stock check** — If `book.stock_quantity < 1`, raise `OutOfStockError(book.id, requested=1, available=book.stock_quantity)`, which maps to HTTP 409 `OUT_OF_STOCK`.

6. **Cart resolution** — Call `await self._cart_repo.find_by_user_id(cmd.user_id)`. If `None`, create a new `CartEntity` with `_id=str(uuid7())`, `_user_id=cmd.user_id`, and an empty `_cart_items` list.

7. **Add book to cart** — Check `cart.find_item_by_book_id(book.id)`. If an existing cart item is found, call `cart.add_item(book, 1)` to increment its quantity by 1. If not found, build a new `CartItemEntity` with `_id=str(uuid7())`, `_cart_id=cart.id`, `_book_id=book.id`, `_quantity=1`, and `_book=book`, then call `cart.append_item(new_cart_item)`.

8. **Remove from wishlist** — Call `wishlist.remove_wishlist_item(cmd.wishlist_item_id)`. This removes the item from `wishlist._wishlist_items` and updates `wishlist._updated_at`.

9. **Persist** — Call `await self._cart_repo.save(cart)` then `await self._wishlist_repo.save(wishlist)`.

10. **Commit** — Call `await self._db_session.commit()`.

11. **Return** — Retrieve the final cart item via `cart.find_item_by_book_id(book.id)` and build `MoveWishlistItemToCartResult(id=..., cart_id=cart.id, book_id=..., quantity=..., book=CartItemBookResult(...))`. The `cover_url` is resolved to a full public URL in the route handler via `build_public_url()`.

---

## Domain Impact

### Entities Involved

| Entity               | Access       | Notes                                                         |
| -------------------- | ------------ | ------------------------------------------------------------- |
| `WishlistEntity`     | Read & Write | Fetched by `user_id`; item removed via `remove_wishlist_item` |
| `WishlistItemEntity` | Read         | Located within the wishlist by `item_id`                      |
| `BookEntity`         | Read         | Fetched fresh via book repo to verify active & in-stock       |
| `CartEntity`         | Read & Write | Fetched by `user_id`; created if absent; item added           |
| `CartItemEntity`     | Write        | Created new or quantity incremented                           |

### Repository Methods Required

| Interface             | Method                           | New?          |
| --------------------- | -------------------------------- | ------------- |
| `IWishlistRepository` | `find_by_user_id(user_id: str)`  | No (existing) |
| `IWishlistRepository` | `save(wishlist: WishlistEntity)` | No (existing) |
| `ICartRepository`     | `find_by_user_id(user_id: str)`  | No (existing) |
| `ICartRepository`     | `save(cart: CartEntity)`         | No (existing) |
| `IBookRepository`     | `find_by_id(book_id, filters)`   | No (existing) |

### New DTOs

| DTO Class                       | Type            | Fields                                                                                 |
| ------------------------------- | --------------- | -------------------------------------------------------------------------------------- |
| `MoveWishlistItemToCartCommand` | Command (input) | `item_id: str`, `user_id: str`                                                         |
| `MoveWishlistItemToCartResult`  | Result (output) | `id: str`, `cart_id: str`, `book_id: str`, `quantity: int`, `book: CartItemBookResult` |

> `CartItemBookResult` already exists in `app/application/dtos/cart_dtos.py` and can be imported directly.

### New Domain Exceptions

_(None — `WishlistNotFoundError`, `WishlistItemNotFoundError`, `BookNotFoundError`, and `OutOfStockError` all exist and are already mapped.)_

### New Error Codes

_(None — all required codes already exist.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/wishlist/04_move_wishlist_item_to_cart/`

| File                             | Scenario                                                                                                                                                                                                          |
| -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_success.bru`                 | Status 201; `data.book_id` matches the moved item's book; `data.quantity` is 1; `meta.requestId` is a string. Depends on `02_add_wishlist_item/01_success.bru` having run first to populate `{{wishlistItemId}}`. |
| `02_wishlist_item_not_found.bru` | Status 404; error code `WISHLIST_ITEM_NOT_FOUND` for a non-existent `item_id`.                                                                                                                                    |

### Pytest Unit Tests

**File:** `backend/tests/unit/test_move_wishlist_item_to_cart.py`

**Happy Path:**

- [x] Returns `MoveWishlistItemToCartResult` with correct `cart_id`, `book_id`, and `quantity=1` when book is active and in stock and the user has no existing cart
- [x] Returns result with incremented quantity when the book is already in the cart
- [x] The wishlist item is absent from the wishlist after a successful move

**Error Cases:**

- [x] Raises `WishlistNotFoundError` when `find_by_user_id` returns `None`
- [x] Raises `WishlistItemNotFoundError` when `item_id` is not in the wishlist
- [x] Raises `BookNotFoundError` when book repo returns `None` for the wishlist item's `book_id`
- [x] Raises `OutOfStockError` when `book.stock_quantity` is 0

**Edge Cases:**

- [x] `db_session.commit` is called exactly once
- [x] A new `CartEntity` is created (not reused) when the user has no cart

---

## Implementation Checklist

- [x] 1. Domain entity — all existing (`WishlistEntity`, `CartEntity`, `CartItemEntity`, `BookEntity`)
- [x] 2. Domain exceptions — all existing and mapped
- [x] 3. Repository interface methods — all existing on `IWishlistRepository`, `ICartRepository`, `IBookRepository`
- [x] 4. DTOs — add `MoveWishlistItemToCartCommand` and `MoveWishlistItemToCartResult` to `app/application/dtos/wishlist_dto.py`
- [x] 5. Use case — create `app/application/use_cases/wishlist/move_wishlist_item_to_cart.py`
- [x] 6. ORM model — not required (no schema change)
- [x] 7. Mapper — not required (no new models)
- [x] 8. Repository implementation — not required (all methods already implemented)
- [x] 9. Exception mapping — not required (all exceptions already mapped)
- [x] 10. Error codes — not required (all codes already exist)
- [x] 11. Pydantic schemas — add `MoveWishlistItemToCartResponse` to `app/presentation/schemas/wishlist_schema.py`
- [x] 12. Route handler — add `POST /wishlist/items/{item_id}/move-to-cart` to `app/presentation/api/app_api/v1/wishlist_routes.py`
- [x] 13. Wire in `deps.py` — `WishlistRepo`, `CartRepo`, `BookRepo`, and `CustomerUser` already wired
- [x] 14. Alembic migration — not required (no schema change)
- [x] 15. Bruno test files — `folder.bru` + `01_success.bru` + `02_wishlist_not_found.bru` + `03_wishlist_item_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_move_wishlist_item_to_cart.py`
