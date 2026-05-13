# Wishlist API Set — Get My Wishlist Proposal

## Overview

| Field        | Value              |
| ------------ | ------------------ |
| API Set      | 10. Wishlist       |
| Use Case     | 1. Get My Wishlist |
| File Index   | 10_01              |
| Access Level | 👤 Customer        |
| Status       | Implemented        |

---

## Endpoint

| Field  | Value                    |
| ------ | ------------------------ |
| Method | GET                      |
| URL    | `/api/app/v1/wishlist`   |
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
    "id": "01932abc-0000-7000-a000-000000000002",
    "items": [
      {
        "id": "01932abc-0000-7000-a000-000000000010",
        "wishlist_id": "01932abc-0000-7000-a000-000000000002",
        "book_id": "01932abc-0000-7000-a000-000000000001",
        "added_at": "2026-05-12T08:00:00Z",
        "book": {
          "id": "01932abc-0000-7000-a000-000000000001",
          "title": "The Name of the Wind",
          "price": "29.99",
          "cover_url": "http://localhost:9000/covers/name-of-the-wind.jpg"
        }
      }
    ]
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-12T08:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                              |
| ----------- | -------------------- | ------------------------------------------------------ |
| 404         | `WISHLIST_NOT_FOUND` | No wishlist exists for this user (never added an item) |

---

## Procedures

1. **Auth guard** — `CustomerUser` dependency decodes the Bearer token, checks the blocklist, and returns the active `UserEntity`. HTTP 401 is raised by `deps.py` if invalid; not handled by the use case.

2. **Wishlist resolution** — Call `await self._wishlist_repo.find_by_user_id(cmd.user_id)`. If the result is `None`, raise `WishlistNotFoundError(cmd.user_id)`, which maps to HTTP 404 `WISHLIST_NOT_FOUND`.

3. **Map items** — For each `WishlistItemEntity` in `wishlist.wishlist_items`, construct a `WishlistItemResult` using the item's fields and its embedded `_book` (already selectin-loaded by `WishlistItemMapper.to_entity`). The `cover_url` is resolved to a full public URL in the route handler via `build_public_url()`.

4. **Return** — Build and return `GetMyWishlistResult(id=wishlist.id, items=[...])`.

No `commit()` is called — this is a read-only operation.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                          |
| -------------------- | ------ | -------------------------------------------------------------- |
| `WishlistEntity`     | Read   | Fetched by `user_id`; raises `WishlistNotFoundError` if absent |
| `WishlistItemEntity` | Read   | Selectin-loaded from `WishlistEntity._wishlist_items`          |
| `BookEntity`         | Read   | Selectin-loaded from `WishlistItemEntity._book`                |

### Repository Methods Required

| Interface             | Method                          | New?          |
| --------------------- | ------------------------------- | ------------- |
| `IWishlistRepository` | `find_by_user_id(user_id: str)` | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                              |
| --------------------- | --------------- | --------------------------------------------------------------------------------------------------- |
| `GetMyWishlistQuery`  | Query (input)   | `user_id: str`                                                                                      |
| `WishlistItemResult`  | Result (nested) | `id: str`, `wishlist_id: str`, `book_id: str`, `added_at: datetime`, `book: WishlistItemBookResult` |
| `GetMyWishlistResult` | Result (output) | `id: str`, `items: list[WishlistItemResult]`                                                        |

> `WishlistItemBookResult` already exists in `wishlist_dto.py`. `WishlistItemResult` shares the same shape as `BaseWishlistItemResult` — implement as a standalone frozen `@dataclass` to keep query-path DTOs independent of mutation-path DTOs.

### New Domain Exceptions

_(None — `WishlistNotFoundError` already exists in `app/domain/exceptions/wishlist.py` and is already mapped to HTTP 404 `WISHLIST_NOT_FOUND` in `exception_mapper.py`.)_

### New Error Codes

_(None — `WISHLIST_NOT_FOUND` already added in 10.2.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/wishlist/01_get_my_wishlist/`

| File                        | Scenario                                                                                                                                                                                             |
| --------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `01_success.bru`            | Status 200; `res.body.success` is `true`; `res.body.data.items` is an array; `meta.requestId` is a string. Depends on `02_add_wishlist_item/01_success.bru` having run first so the wishlist exists. |
| `02_wishlist_not_found.bru` | Status 404; error code `WISHLIST_NOT_FOUND` for a user with no wishlist yet.                                                                                                                         |

> `01_success.bru` assumes the wishlist already exists (created by a prior add). `02_wishlist_not_found.bru` requires a fresh user token with no wishlist history.

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_my_wishlist.py`

**Happy Path:**

- [x] `GetMyWishlistUseCase.execute(cmd)` returns `GetMyWishlistResult` with correct `id` and populated `items` list when a wishlist with items exists
- [x] Returns `GetMyWishlistResult` with `items=[]` when wishlist exists but has no items

**Error Cases:**

- [x] Raises `WishlistNotFoundError` when `find_by_user_id` returns `None`

**Edge Cases:**

- [x] `db_session.commit` is never called (read-only operation)
- [x] Each item in `result.items` has the embedded `book.title` correctly mapped

---

## Implementation Checklist

- [x] 1. Domain entity — `WishlistEntity` and `WishlistItemEntity` already exist
- [x] 2. Domain exceptions — `WishlistNotFoundError` already exists and is mapped
- [x] 3. Repository interface — `IWishlistRepository.find_by_user_id` already exists
- [x] 4. DTOs — add `GetMyWishlistCommand`, `WishlistItemResult`, `GetMyWishlistResult` to `app/application/dtos/wishlist_dto.py`
- [x] 5. Use case — create `app/application/use_cases/wishlist/get_my_wishlist.py` (`GetMyWishlistUseCase`)
- [x] 6. ORM model — `WishlistModel` and `WishlistItemModel` already exist; no migration needed
- [x] 7. Mapper — `WishlistMapper` and `WishlistItemMapper` already exist and verified
- [x] 8. Repository implementation — `WishlistRepositoryImpl.find_by_user_id` already implemented
- [x] 9. Exception mapping — `WishlistNotFoundError → (404, WISHLIST_NOT_FOUND)` already mapped
- [x] 10. Error codes — `WISHLIST_NOT_FOUND` already exists
- [x] 11. Pydantic schemas — add `WishlistItemResponse` and `GetMyWishlistResponse` to `app/presentation/schemas/wishlist_schema.py`
- [x] 12. Route handler — add `GET /wishlist` to `app/presentation/api/app_api/v1/wishlist_routes.py`
- [x] 13. Wire in `deps.py` — `WishlistRepo` and `CustomerUser` already wired from 10.2
- [x] 14. Alembic migration — not required (tables already exist)
- [x] 15. Bruno test files — `folder.bru` + `01_success.bru` + `02_wishlist_not_found.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_get_my_wishlist.py`
