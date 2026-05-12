# Wishlist API Set — Add Wishlist Item Proposal

## Overview

| Field        | Value                |
| ------------ | -------------------- |
| API Set      | 10. Wishlist         |
| Use Case     | 2. Add Wishlist Item |
| File Index   | 10_02                |
| Access Level | 👤 Customer          |
| Status       | Implemented          |

---

## Endpoint

| Field  | Value                        |
| ------ | ---------------------------- |
| Method | POST                         |
| URL    | `/api/app/v1/wishlist/items` |
| Auth   | Bearer token (USER role)     |

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

| Field   | Type   | Required | Constraints              |
| ------- | ------ | -------- | ------------------------ |
| book_id | string | Yes      | UUID of an existing book |

**Example:**

```json
{
  "book_id": "01932abc-0000-7000-a000-000000000001"
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
    "id": "01932abc-0000-7000-a000-000000000010",
    "wishlist_id": "01932abc-0000-7000-a000-000000000002",
    "book_id": "01932abc-0000-7000-a000-000000000001",
    "added_at": "2026-05-12T08:00:00Z",
    "book": {
      "id": "01932abc-0000-7000-a000-000000000001",
      "title": "The Name of the Wind",
      "price": "29.99",
      "cover_url": "covers/name-of-the-wind.jpg"
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-12T08:00:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                     | Condition                                                  |
| ----------- | ------------------------------ | ---------------------------------------------------------- |
| 401         | `UNAUTHORIZED`                 | No Authorization header provided                           |
| 401         | `TOKEN_EXPIRED`                | Bearer token is expired                                    |
| 401         | `INVALID_TOKEN`                | Bearer token is invalid or malformed                       |
| 404         | `BOOK_NOT_FOUND`               | No active (non-deleted, non-deactivated) book with that ID |
| 409         | `WISHLIST_ITEM_ALREADY_EXISTS` | That book is already in the user's wishlist                |
| 422         | `VALIDATION_ERROR`             | Pydantic validation failure (e.g. book_id not a UUID)      |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency decodes the Bearer token, checks the blocklist, and returns the active `UserEntity`. HTTP 401 is raised by `deps.py` if invalid; not handled by the use case.

2. **Input validation** — FastAPI validates the `AddWishlistItemRequest` Pydantic schema. HTTP 422 is returned automatically if `book_id` is missing or not a valid UUID string.

3. **Book existence check** — Call `await self._book_repo.find_by_id(cmd.book_id, BookStatusFilter(status="activate"))` to verify the book exists and is active (not deleted, not deactivated). If the result is `None`, raise `BookNotFoundError(cmd.book_id)`, which maps to HTTP 404 `BOOK_NOT_FOUND`.

4. **Wishlist resolution** — Call `await self._wishlist_repo.find_by_user_id(cmd.user_id)`. If `None`, create a new `WishlistEntity` with `_id=str(uuid7())`, `_user_id=cmd.user_id`, `_created_at=now`, `_updated_at=now`, `_wishlist_items=[]`.

5. **Duplicate check** — Call `wishlist.add_wishlist_item(new_item)`. The `WishlistEntity.add_wishlist_item()` method already checks if a `WishlistItemEntity` with the same `book_id` is present and raises `ValueError` if so. The use case must catch that `ValueError` and re-raise it as `WishlistItemAlreadyExistsError(cmd.book_id)`, which maps to HTTP 409 `WISHLIST_ITEM_ALREADY_EXISTS`.

6. **Build the new item** — Before calling `add_wishlist_item`, construct the `WishlistItemEntity`:

   ```
   now = datetime.now(UTC)
   new_item = WishlistItemEntity(
       _id=str(uuid7()),
       _wishlist_id=wishlist.id,
       _book_id=book.id,
       _added_at=now,
       _created_at=now,
       _updated_at=now,
       _book=book,
   )
   ```

   Then call `wishlist.add_wishlist_item(new_item)` wrapped in the `try/except ValueError` from step 5.

7. **Persist** — Call `await self._wishlist_repo.save(wishlist)`. The repository must not call `commit()`.

8. **Commit** — Call `await self._db_session.commit()` in the use case, after the save completes.

9. **Return** — Build and return `AddWishlistItemResult` using the fields of `new_item` and the resolved `book` entity.

---

## Domain Impact

### Entities Involved

| Entity               | Access       | Notes                                         |
| -------------------- | ------------ | --------------------------------------------- |
| `WishlistEntity`     | Read / Write | Created lazily if no wishlist exists for user |
| `WishlistItemEntity` | Write        | New item appended via `add_wishlist_item()`   |
| `BookEntity`         | Read         | Verified active; embedded in result           |

### Repository Methods Required

| Interface             | Method                               | New?                |
| --------------------- | ------------------------------------ | ------------------- |
| `IWishlistRepository` | `find_by_user_id(user_id: str)`      | Yes (new interface) |
| `IWishlistRepository` | `save(wishlist: WishlistEntity)`     | Yes                 |
| `IBookRepository`     | `find_by_id(book_id, status_filter)` | No (existing)       |

### New DTOs

| DTO Class                | Type            | Fields                                                                                              |
| ------------------------ | --------------- | --------------------------------------------------------------------------------------------------- |
| `AddWishlistItemCommand` | Command (input) | `book_id: str`, `user_id: str`                                                                      |
| `WishlistItemBookResult` | Result (nested) | `id: str`, `title: str`, `price: Decimal`, `cover_url: str \| None`                                 |
| `AddWishlistItemResult`  | Result (output) | `id: str`, `wishlist_id: str`, `book_id: str`, `added_at: datetime`, `book: WishlistItemBookResult` |

### New Domain Exceptions

| Exception Class                  | File                                | Inherits          |
| -------------------------------- | ----------------------------------- | ----------------- |
| `WishlistItemAlreadyExistsError` | `app/domain/exceptions/wishlist.py` | `DomainException` |
| `WishlistNotFoundError`          | `app/domain/exceptions/wishlist.py` | `DomainException` |

_(`WishlistNotFoundError` is added now since it will be needed by upcoming wishlist endpoints.)_

### New Error Codes

| Constant                       | Value                            | Description                            |
| ------------------------------ | -------------------------------- | -------------------------------------- |
| `WISHLIST_ITEM_ALREADY_EXISTS` | `"WISHLIST_ITEM_ALREADY_EXISTS"` | Book is already in the user's wishlist |
| `WISHLIST_NOT_FOUND`           | `"WISHLIST_NOT_FOUND"`           | No wishlist found for the given user   |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/wishlist/02_add_wishlist_item/`

| File                         | Scenario                                                                                                                  |
| ---------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| `01_success.bru`             | Status 201; `res.body.success` is `true`; `res.body.data.book_id` matches request; `res.body.data.book.title` is a string |
| `02_book_not_found.bru`      | Status 404; error code `BOOK_NOT_FOUND` for a non-existent book_id                                                        |
| `03_already_in_wishlist.bru` | Status 409; error code `WISHLIST_ITEM_ALREADY_EXISTS` on duplicate add                                                    |

### Pytest Unit Tests

**File:** `backend/tests/unit/test_add_wishlist_item.py`

**Happy Path:**

- [x] `AddWishlistItemUseCase.execute(valid_command)` returns `AddWishlistItemResult` with correct `book_id`, `wishlist_id`, and non-null `book` fields when the wishlist does not yet exist (lazy creation)
- [x] Returns `AddWishlistItemResult` with correct fields when the wishlist already exists and the book is not yet in it

**Error Cases:**

- [x] Raises `BookNotFoundError` when `book_repo.find_by_id` returns `None`
- [x] Raises `WishlistItemAlreadyExistsError` when the book is already in the wishlist

**Edge Cases:**

- [x] A new `WishlistEntity` is created (with a UUIDv7 `id`) when `find_by_user_id` returns `None`
- [x] The newly created `WishlistItemEntity` has `added_at` set to a non-null datetime

---

## Implementation Checklist

- [x] 1. Domain entity — `WishlistEntity` and `WishlistItemEntity` already exist
- [x] 2. Domain exceptions — create `app/domain/exceptions/wishlist.py` with `WishlistItemAlreadyExistsError` and `WishlistNotFoundError`; export from `__init__.py`
- [x] 3. Repository interface — create `app/domain/repositories/wishlist_repository.py` with `IWishlistRepository` (`find_by_user_id`, `save`)
- [x] 4. DTOs — add `AddWishlistItemCommand`, `WishlistItemBookResult`, `AddWishlistItemResult` to `app/application/dtos/wishlist_dtos.py` (new file)
- [x] 5. Use case — `app/application/use_cases/wishlist/add_wishlist_item.py` (`AddWishlistItemUseCase`)
- [x] 6. ORM model — `WishlistModel` and `WishlistItemModel` already exist; no migration needed
- [x] 7. Mapper — `WishlistMapper` and `WishlistItemMapper` already exist; verify `to_entity`/`to_model` coverage
- [x] 8. Repository implementation — create `app/infrastructure/db/repositories/wishlist_repository_impl.py` (`WishlistRepositoryImpl` implementing `IWishlistRepository`)
- [x] 9. Exception mapping — add `WishlistItemAlreadyExistsError → (409, WISHLIST_ITEM_ALREADY_EXISTS)` and `WishlistNotFoundError → (404, WISHLIST_NOT_FOUND)` to `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `WISHLIST_ITEM_ALREADY_EXISTS` and `WISHLIST_NOT_FOUND` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — create `app/presentation/schemas/wishlist_schema.py` with `AddWishlistItemRequest` and `AddWishlistItemResponse`
- [x] 12. Route handler — create `app/presentation/api/app_api/v1/wishlist_routes.py`; register in `v1/__init__.py`
- [x] 13. Wire in `deps.py` — add `get_wishlist_repository` provider and `WishlistRepo` typed alias
- [x] 14. Alembic migration — not required (tables already exist)
- [x] 15. Bruno test files — `folder.bru` + `01_success.bru` through `03_already_in_wishlist.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_add_wishlist_item.py`
