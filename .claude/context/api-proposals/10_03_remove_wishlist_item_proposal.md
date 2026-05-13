# Wishlist API Set — Remove Wishlist Item Proposal

## Overview

| Field        | Value                   |
| ------------ | ----------------------- |
| API Set      | 10. Wishlist            |
| Use Case     | 3. Remove Wishlist Item |
| File Index   | 10_03                   |
| Access Level | 👤 Customer             |
| Status       | Implemented             |

---

## Endpoint

| Field  | Value                                  |
| ------ | -------------------------------------- |
| Method | DELETE                                 |
| URL    | `/api/app/v1/wishlist/items/{item_id}` |
| Auth   | Bearer token (USER role)               |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description                              |
| --------- | ------------- | ---------------------------------------- |
| `item_id` | string (UUID) | ID of the `WishlistItemEntity` to remove |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 204 No Content

_(No response body — `ResponseFormatterMiddleware` passes through 204 responses unchanged.)_

### Error Responses

| HTTP Status | Error Code                | Condition                                                        |
| ----------- | ------------------------- | ---------------------------------------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`      | Missing, expired, or revoked Bearer token                        |
| 404         | `WISHLIST_NOT_FOUND`      | Authenticated user has no wishlist (never added an item)         |
| 404         | `WISHLIST_ITEM_NOT_FOUND` | `item_id` does not exist within the user's wishlist              |
| 422         | `UNPROCESSABLE_ENTITY`    | Pydantic validation failure (e.g. `item_id` is not a valid UUID) |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency in `deps.py` decodes the Bearer token, checks the blocklist, and returns the active `UserEntity`. HTTP 401 is raised by the dependency if the token is invalid or revoked; the use case is not involved.

2. **Wishlist resolution** — Call `await self._wishlist_repo.find_by_user_id(cmd.user_id)`. If the result is `None`, raise `WishlistNotFoundError(cmd.user_id)`, which maps to HTTP 404 `WISHLIST_NOT_FOUND`.

3. **Item existence check** — Search `wishlist.wishlist_items` for an item whose `id == cmd.item_id`. If no matching item is found, raise `WishlistItemNotFoundError(cmd.item_id)`, which maps to HTTP 404 `WISHLIST_ITEM_NOT_FOUND`. This also implicitly enforces ownership — only items belonging to this user's wishlist are reachable.

4. **Remove item** — Call `wishlist.remove_wishlist_item(cmd.item_id)`. The entity removes the item from `_wishlist_items` and updates `_updated_at` internally.

5. **Persist** — Call `await self._wishlist_repo.save(wishlist)`. The repository does not commit.

6. **Commit** — Call `await self._db_session.commit()` in the use case, completing the unit of work.

7. **Return** — Return `None`. The route handler responds with HTTP 204 No Content.

---

## Domain Impact

### Entities Involved

| Entity               | Access       | Notes                                                          |
| -------------------- | ------------ | -------------------------------------------------------------- |
| `WishlistEntity`     | Read / Write | Loaded by `user_id`; `remove_wishlist_item()` mutates the list |
| `WishlistItemEntity` | Read / Write | Removed from `WishlistEntity._wishlist_items`; selectin-loaded |

### Repository Methods Required

| Interface             | Method                           | New?          |
| --------------------- | -------------------------------- | ------------- |
| `IWishlistRepository` | `find_by_user_id(user_id: str)`  | No (existing) |
| `IWishlistRepository` | `save(wishlist: WishlistEntity)` | No (existing) |

### New DTOs

| DTO Class                   | Type            | Fields                         |
| --------------------------- | --------------- | ------------------------------ |
| `RemoveWishlistItemCommand` | Command (input) | `item_id: str`, `user_id: str` |

_(No result DTO — use case returns `None`.)_

### New Domain Exceptions

_(None — `WishlistNotFoundError` and `WishlistItemNotFoundError` already exist in `app/domain/exceptions/wishlist.py` and are already mapped.)_

### New Error Codes

_(None — `WISHLIST_NOT_FOUND` and `WISHLIST_ITEM_NOT_FOUND` already exist in `app/application/errors/error_codes.py`.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/wishlist/03_remove_wishlist_item/`

**`01_success.bru` — Happy Path:**

- [x] Status 204 No Content
- [x] Response body is empty
- [x] Subsequent `GET /wishlist` no longer returns the removed item

**Error Cases:**

- [x] `02_wishlist_not_found.bru` — Status 404 with error code `WISHLIST_NOT_FOUND` for a user who has never added any item
- [x] `03_item_not_found.bru` — Status 404 with error code `WISHLIST_ITEM_NOT_FOUND` when `item_id` does not belong to the user's wishlist

### Pytest Unit Tests

**File:** `backend/tests/unit/test_remove_wishlist_item.py`

**Happy Path:**

- [x] `RemoveWishlistItemUseCase.execute(cmd)` returns `None` and calls `save` + `commit` when item exists in the user's wishlist

**Error Cases:**

- [x] Raises `WishlistNotFoundError` when `find_by_user_id` returns `None`
- [x] Raises `WishlistItemNotFoundError` when `item_id` is not present in the wishlist's items list

**Edge Cases:**

- [x] `wishlist_repo.save` is called with the mutated wishlist (item removed from `_wishlist_items`)
- [x] `db_session.commit` is called exactly once on success, and not called when an exception is raised

---

## Implementation Checklist

- [x] 1. Domain entity — `WishlistEntity.remove_wishlist_item()` already implemented
- [x] 2. Domain exceptions — `WishlistNotFoundError` and `WishlistItemNotFoundError` already exist and are mapped
- [x] 3. Repository interface — `find_by_user_id` and `save` already exist on `IWishlistRepository`
- [x] 4. DTOs — add `RemoveWishlistItemCommand` to `app/application/dtos/wishlist_dto.py`
- [x] 5. Use case — create `app/application/use_cases/wishlist/remove_wishlist_item.py` (`RemoveWishlistItemUseCase`)
- [x] 6. ORM model — `WishlistModel` and `WishlistItemModel` already exist; no migration needed
- [x] 7. Mapper — `WishlistMapper` and `WishlistItemMapper` already exist and verified
- [x] 8. Repository implementation — `find_by_user_id` and `save` already implemented in `WishlistRepositoryImpl`
- [x] 9. Exception mapping — both exceptions already mapped in `exception_mapper.py`
- [x] 10. Error codes — `WISHLIST_NOT_FOUND` and `WISHLIST_ITEM_NOT_FOUND` already exist
- [x] 11. Pydantic schemas — no new schema needed (204 has no body); existing schemas unaffected
- [x] 12. Route handler — add `DELETE /wishlist/items/{item_id}` to `app/presentation/api/app_api/v1/wishlist_routes.py`
- [x] 13. Wire in `deps.py` — `WishlistRepo` and `CustomerUser` already wired
- [x] 14. Alembic migration — not required (no schema changes)
- [x] 15. Bruno test files — `folder.bru` + `01_success.bru` + four error case files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_remove_wishlist_item.py`
