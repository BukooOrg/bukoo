# Book Catalog — Update Book Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 4. Book Catalog |
| Use Case     | 4. Update Book  |
| File Index   | 04_04           |
| Access Level | 🔑 Admin        |
| Status       | Implemented     |

---

## Endpoint

| Field  | Value                         |
| ------ | ----------------------------- |
| Method | PATCH                         |
| URL    | `/api/app/v1/books/{book_id}` |
| Auth   | Bearer token (ADMIN role)     |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description              |
| --------- | ------------- | ------------------------ |
| book_id   | string (UUID) | ID of the book to update |

### Query Parameters

_(None)_

### Request Body

All fields are optional. Only provided fields are updated (partial update semantics).

| Field          | Type            | Required | Constraints                                                                  |
| -------------- | --------------- | -------- | ---------------------------------------------------------------------------- |
| title          | string          | No       | 1–500 characters                                                             |
| price          | decimal         | No       | > 0, 2 decimal places                                                        |
| stock_quantity | integer         | No       | ≥ 0                                                                          |
| language       | string          | No       | 1–100 characters                                                             |
| isbn           | string \| null  | No       | Valid ISBN-13, or null to clear                                              |
| description    | string \| null  | No       | max 5000 characters, or null                                                 |
| page_count     | integer \| null | No       | ≥ 1, or null to clear                                                        |
| published_date | date \| null    | No       | ISO 8601 date, or null to clear                                              |
| publisher_id   | string \| null  | No       | UUID of existing publisher, or null                                          |
| category_id    | string \| null  | No       | UUID of existing category, or null                                           |
| authors        | array \| null   | No       | Replaces the full author list; null means no change; `[]` clears all authors |

Each item in `authors`:

| Field         | Type    | Required | Constraints                |
| ------------- | ------- | -------- | -------------------------- |
| author_id     | string  | Yes      | UUID of an existing author |
| display_order | integer | Yes      | ≥ 1                        |

**Example:**

```json
{
  "title": "The Pragmatic Programmer (20th Anniversary Edition)",
  "price": "49.99",
  "language": "English",
  "isbn": "9780135957059",
  "publisher_id": "01932abc-0001-7000-0000-000000000001",
  "authors": [
    { "author_id": "01932abc-0001-7000-0000-000000000002", "display_order": 1 },
    { "author_id": "01932abc-0001-7000-0000-000000000003", "display_order": 2 }
  ]
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
    "id": "01932abc-...",
    "title": "The Pragmatic Programmer (20th Anniversary Edition)",
    "price": "49.99",
    "language": "English",
    "stock_quantity": 100,
    "cover_url": null,
    "isbn": "9780135957059",
    "description": null,
    "page_count": null,
    "published_date": null,
    "is_active": true,
    "publisher": { "id": "...", "name": "Addison-Wesley" },
    "category": null,
    "authors": [
      { "id": "...", "name": "David Thomas", "display_order": 1 },
      { "id": "...", "name": "Andrew Hunt", "display_order": 2 }
    ],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-11T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                            |
| ----------- | -------------------- | ---------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | Missing or invalid Bearer token                      |
| 403         | PERMISSION_DENIED    | Authenticated user does not have ADMIN role          |
| 404         | BOOK_NOT_FOUND       | No active book with the given `book_id`              |
| 404         | AUTHOR_NOT_FOUND     | One of the provided `author_id` values doesn't exist |
| 404         | PUBLISHER_NOT_FOUND  | The provided `publisher_id` doesn't exist            |
| 404         | CATEGORY_NOT_FOUND   | The provided `category_id` doesn't exist             |
| 409         | BOOK_ALREADY_EXISTS  | Another book already has the submitted ISBN          |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure                          |

---

## Procedures

1. **Auth guard** — `AdminUser` dependency validates the Bearer token and asserts `UserRole.ADMIN`. FastAPI raises HTTP 401 or 403 before the use case runs if the guard fails.

2. **Input validation** — Pydantic schema validates the request body. Any field-level constraint violation (e.g. `price ≤ 0`, `title` empty) returns HTTP 422 automatically.

3. **Fetch book** — Call `book_repo.find_by_id(book_id, filters=BookStatusFilter(status="all"))` to find the book regardless of its activation state. If `None` is returned, raise `BookNotFoundError(book_id)`.

4. **ISBN uniqueness check** — If `isbn` is present in the request and differs from the book's current ISBN, call `book_repo.find_by_isbn(isbn)`. If a result is returned and its `id != book.id`, raise `BookAlreadyExistsError(isbn)`.

5. **Publisher resolution** — If `publisher_id` is present in the request (including explicit `null` to clear it): if it is a non-null UUID, call `publisher_repo.find_by_id(publisher_id)`; if `None` is returned, raise `PublisherNotFoundError(publisher_id)`.

6. **Category resolution** — If `category_id` is present in the request: if it is a non-null UUID, call `category_repo.find_by_id(category_id)`; if `None` is returned, raise `CategoryNotFoundError(category_id)`.

7. **Author resolution** — If `authors` is present in the request (not omitted), fetch each `author_id` via `author_repo.find_by_id(author_id)`. If any author is `None`, raise `AuthorNotFoundError(author_id)`. Collect results into a dict keyed by `author_id`.

8. **Apply scalar field updates** — For each field provided in the command (`title`, `price`, `stock_quantity`, `language`, `isbn`, `description`, `page_count`, `published_date`), update the corresponding private attribute on `BookEntity` directly and set `book._updated_at = datetime.now(UTC)`. (These are simple assignments — no domain method exists yet for them; a single `update()` entity method should be added to `BookEntity` to keep mutation inside the entity boundary.)

9. **Apply publisher update** — If `publisher_id` was in the request: if a `PublisherEntity` was resolved, call `book.set_publisher(publisher)`; if the value was `null`, set `book._publisher = None` and `book._publisher_id = None` and `book._updated_at = datetime.now(UTC)`.

10. **Apply category update** — If `category_id` was in the request: if a `CategoryEntity` was resolved, call `book.set_category(category)`; if the value was `null`, set `book._category = None` and `book._category_id = None` and `book._updated_at = datetime.now(UTC)`.

11. **Apply author list replacement** — If `authors` was present in the request, clear the current author list (`book._authors = []`) and then, for each item in the new list, construct a `BookAuthorEntity` and call `book.set_author(book_author)` (same pattern as `CreateBookUseCase`). If the `authors` list was `[]`, the book ends up with no authors.

12. **Persist** — Call `await book_repo.save(book)`. The repository uses `session.merge(model)` — no commit here.

13. **Commit** — Call `await self._db_session.commit()`.

14. **Return** — Build and return `UpdateBookResult` using the shared `_to_result(book, UpdateBookResult)` helper from `BaseBookUseCase`.

---

## Domain Impact

### Entities Involved

| Entity             | Access       | Notes                                        |
| ------------------ | ------------ | -------------------------------------------- |
| `BookEntity`       | Read / Write | Primary entity being mutated                 |
| `BookAuthorEntity` | Write        | Author list replaced via `book.set_author()` |
| `PublisherEntity`  | Read         | Resolved for existence check only            |
| `CategoryEntity`   | Read         | Resolved for existence check only            |
| `AuthorEntity`     | Read         | Each author_id resolved for existence check  |

### Repository Methods Required

| Interface              | Method                         | New?          |
| ---------------------- | ------------------------------ | ------------- |
| `IBookRepository`      | `find_by_id(book_id, filters)` | No (existing) |
| `IBookRepository`      | `find_by_isbn(isbn)`           | No (existing) |
| `IBookRepository`      | `save(book)`                   | No (existing) |
| `IPublisherRepository` | `find_by_id(publisher_id)`     | No (existing) |
| `ICategoryRepository`  | `find_by_id(category_id)`      | No (existing) |
| `IAuthorRepository`    | `find_by_id(author_id)`        | No (existing) |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                                                                                                                   |
| ---------------------- | --------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `UpdateBookAuthorItem` | Command (input) | `author_id: str`, `display_order: int`                                                                                                                                                                   |
| `UpdateBookCommand`    | Command (input) | All fields optional: `title`, `price`, `stock_quantity`, `language`, `isbn`, `description`, `page_count`, `published_date`, `publisher_id`, `category_id`, `authors: list[UpdateBookAuthorItem] \| None` |
| `UpdateBookResult`     | Result (output) | Inherits `BaseBookResult` (same shape as `CreateBookResult`)                                                                                                                                             |

### New Domain Exceptions

_(None — all required exceptions already exist: `BookNotFoundError`, `BookAlreadyExistsError`, `AuthorNotFoundError`, `PublisherNotFoundError`, `CategoryNotFoundError`)_

### New Error Codes

_(None — all required error codes are already mapped)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book-catalog/update-book/`

| File                             | Scenario                                                                   |
| -------------------------------- | -------------------------------------------------------------------------- |
| `01_success.bru`                 | 200 OK — partial update (title + price); verify updated fields in response |
| `02_success_clear_publisher.bru` | 200 OK — `publisher_id: null` clears the publisher                         |
| `03_success_replace_authors.bru` | 200 OK — `authors` list replaced with new set                              |
| `04_forbidden_non_admin.bru`     | 403 when token belongs to a USER-role account                              |
| `05_book_not_found.bru`          | 404 `BOOK_NOT_FOUND` when `book_id` does not exist                         |
| `06_isbn_conflict.bru`           | 409 `BOOK_ALREADY_EXISTS` when the given ISBN belongs to another book      |
| `07_author_not_found.bru`        | 404 `AUTHOR_NOT_FOUND` when one `author_id` doesn't exist                  |
| `08_publisher_not_found.bru`     | 404 `PUBLISHER_NOT_FOUND` when `publisher_id` doesn't exist                |
| `09_category_not_found.bru`      | 404 `CATEGORY_NOT_FOUND` when `category_id` doesn't exist                  |
| `10_validation_error.bru`        | 422 when `price` is zero or `title` is empty                               |

### Pytest Unit Tests

**File:** `backend/tests/unit/test_update_book.py`

**Happy Path:**

- [ ] `UpdateBookUseCase.execute(valid_command)` returns `UpdateBookResult` with only updated fields changed
- [ ] When `authors` is omitted, existing authors are preserved
- [ ] When `authors` is `[]`, book ends with empty author list
- [ ] When `publisher_id` is `null`, book's `publisher` and `publisher_id` are cleared

**Error Cases:**

- [ ] Raises `BookNotFoundError` when `book_id` does not exist
- [ ] Raises `BookAlreadyExistsError` when `isbn` belongs to a different book
- [ ] Raises `AuthorNotFoundError` when any `author_id` in the list doesn't exist
- [ ] Raises `PublisherNotFoundError` when `publisher_id` doesn't exist
- [ ] Raises `CategoryNotFoundError` when `category_id` doesn't exist

**Edge Cases:**

- [ ] ISBN uniqueness check is skipped when submitted ISBN equals the book's current ISBN
- [ ] A command with no fields set leaves the book entity unchanged (all fields remain as-is)

---

## Implementation Checklist

- [x] 1. Domain entity — add `update()` method to `BookEntity` for scalar field mutations (`app/domain/entities/book_entity.py`)
- [x] 2. Domain exceptions — none new; all exist
- [x] 3. Repository interface methods — none new; all exist on `IBookRepository`, `IPublisherRepository`, `ICategoryRepository`, `IAuthorRepository`
- [x] 4. DTOs — add `UpdateBookCommand`, `UpdateBookAuthorItem`, `UpdateBookResult` to `app/application/dtos/book_dto.py`
- [x] 5. Use case — `app/application/use_cases/book/update_book.py` (`UpdateBookUseCase`)
- [x] 6. ORM model — no changes (existing `BookModel` and `BookAuthorModel`)
- [x] 7. Mapper — no changes
- [x] 8. Repository implementation — no changes
- [x] 9. Exception mapping — no changes
- [x] 10. Error codes — no changes
- [x] 11. Pydantic schemas — add `UpdateBookAuthorItemRequest`, `UpdateBookRequest`, `UpdateBookResponse` to `app/presentation/schemas/book_schema.py`
- [x] 12. Route handler — add `PATCH /{book_id}` handler to `app/presentation/api/app_api/v1/book_routes.py`
- [x] 13. Wire in `deps.py` — no changes (all repos already wired)
- [x] 14. Alembic migration — none (no schema changes)
- [x] 15. Bruno test files — `bruno/book/update_book/folder.bru` + 10 `.bru` files as listed above
- [x] 16. Pytest unit tests — `backend/tests/unit/test_update_book.py`
