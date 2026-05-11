# Book Catalog — Create Book Proposal

## Overview

| Field        | Value           |
| ------------ | --------------- |
| API Set      | 4. Book Catalog |
| Use Case     | 3. Create Book  |
| File Index   | 04_03           |
| Access Level | 🔑 Admin        |
| Status       | Implemented     |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | POST                      |
| URL    | `/api/app/v1/books`       |
| Auth   | Bearer token (ADMIN role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | Yes      | application/json      |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_None_

### Query Parameters

_None_

### Request Body

| Field            | Type             | Required | Constraints                                               |
| ---------------- | ---------------- | -------- | --------------------------------------------------------- |
| `title`          | string           | Yes      | 1–500 characters                                          |
| `price`          | number (decimal) | Yes      | > 0, max 2 decimal places                                 |
| `stock_quantity` | integer          | Yes      | >= 0                                                      |
| `language`       | string           | Yes      | 1–100 characters                                          |
| `isbn`           | string           | No       | Must be a valid ISBN-13 (13 digits, checksum)             |
| `description`    | string           | No       | Max 5000 characters                                       |
| `page_count`     | integer          | No       | >= 1                                                      |
| `published_date` | string (date)    | No       | ISO 8601 date: `YYYY-MM-DD`                               |
| `publisher_id`   | string (UUID)    | No       | Must refer to an existing publisher                       |
| `category_id`    | string (UUID)    | No       | Must refer to an existing category                        |
| `authors`        | array of object  | No       | Each item: `{ author_id: UUID, display_order: int >= 1 }` |

**Example:**

```json
{
  "title": "The Pragmatic Programmer",
  "price": 49.99,
  "stock_quantity": 120,
  "language": "English",
  "isbn": "9780135957059",
  "description": "Your journey to mastery.",
  "page_count": 352,
  "published_date": "2019-09-13",
  "publisher_id": "019324ab-0000-7000-0000-000000000001",
  "category_id": "019324ab-0000-7000-0000-000000000002",
  "authors": [
    { "author_id": "019324ab-0000-7000-0000-000000000003", "display_order": 1 },
    { "author_id": "019324ab-0000-7000-0000-000000000004", "display_order": 2 }
  ]
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
    "id": "019324ab-0000-7000-0000-000000000010",
    "title": "The Pragmatic Programmer",
    "price": "49.99",
    "stock_quantity": 120,
    "language": "English",
    "isbn": "9780135957059",
    "description": "Your journey to mastery.",
    "page_count": 352,
    "published_date": "2019-09-13",
    "cover_url": null,
    "is_active": true,
    "publisher": {
      "id": "019324ab-0000-7000-0000-000000000001",
      "name": "Addison-Wesley"
    },
    "category": {
      "id": "019324ab-0000-7000-0000-000000000002",
      "name": "Software Engineering"
    },
    "authors": [
      {
        "id": "019324ab-0000-7000-0000-000000000003",
        "name": "David Thomas",
        "display_order": 1
      },
      {
        "id": "019324ab-0000-7000-0000-000000000004",
        "name": "Andrew Hunt",
        "display_order": 2
      }
    ],
    "created_at": "2026-05-11T10:30:00Z",
    "updated_at": "2026-05-11T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-11T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code              | Condition                                                                  |
| ----------- | ----------------------- | -------------------------------------------------------------------------- |
| 401         | `UNAUTHORIZED`          | No Authorization header or token is missing                                |
| 401         | `TOKEN_EXPIRED`         | Bearer token is expired                                                    |
| 401         | `INVALID_TOKEN`         | Bearer token is malformed or signature invalid                             |
| 403         | `ADMIN_ACCESS_REQUIRED` | Authenticated user has `USER` role, not `ADMIN`                            |
| 409         | `BOOK_ALREADY_EXISTS`   | A non-deleted book with the same ISBN already exists                       |
| 404         | `PUBLISHER_NOT_FOUND`   | `publisher_id` does not refer to an existing publisher                     |
| 404         | `CATEGORY_NOT_FOUND`    | `category_id` does not refer to an existing category                       |
| 404         | `AUTHOR_NOT_FOUND`      | One of the `author_id` values does not exist                               |
| 422         | `INVALID_ISBN`          | `isbn` fails ISBN-13 checksum validation                                   |
| 422         | `UNPROCESSABLE_ENTITY`  | Pydantic validation failure (missing required fields, type mismatch, etc.) |

---

## Procedures

1. **Auth guard.** The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the blocklist via `RedisCacheService`, loads the `UserEntity`, and asserts `user.role == UserRole.ADMIN`. If the token is invalid/expired or the role is not ADMIN, FastAPI rejects the request before the use case is reached.

2. **Input validation.** FastAPI automatically validates the Pydantic request schema. Missing required fields or type mismatches return HTTP 422 before the use case executes.

3. **ISBN uniqueness check.** If `isbn` is provided, call `book_repo.find_by_isbn(isbn) -> BookEntity | None`. If a record is returned, raise `BookAlreadyExistsError(isbn)` → HTTP 409 `BOOK_ALREADY_EXISTS`.

4. **Publisher existence check.** If `publisher_id` is provided, call `publisher_repo.find_by_id(publisher_id) -> PublisherEntity | None`. If `None`, raise `PublisherNotFoundError(publisher_id)` → HTTP 404 `PUBLISHER_NOT_FOUND`.

5. **Category existence check.** If `category_id` is provided, call `category_repo.find_by_id(category_id) -> CategoryEntity | None`. If `None`, raise `CategoryNotFoundError(category_id)` → HTTP 404 `CATEGORY_NOT_FOUND`.

6. **Author existence checks.** For each item in the `authors` list, call `author_repo.find_by_id(author_id) -> AuthorEntity | None`. If any returns `None`, raise `AuthorNotFoundError(author_id)` → HTTP 404 `AUTHOR_NOT_FOUND`. Collect all resolved `AuthorEntity` objects keyed by `author_id` for use in step 9.

7. **Construct `BookEntity`.** Instantiate `BookEntity` with `_id=str(uuid7())`, all scalar fields from the command (`_title`, `_price`, `_stock_quantity`, `_language`, `_isbn`, `_description`, `_page_count`, `_published_date`, `_publisher_id`, `_category_id`), `_deactivated_at=None`, `_cover_url=None`, and `_created_at=_updated_at=datetime.now(UTC)`, `_deleted_at=None`.

8. **Associate authors.** For each `{ author_id, display_order }` in the command, create a `BookAuthorEntity` with `_book_id=book.id`, `_author_id=author_id`, `_display_order=display_order`, and `_created_at=_updated_at=datetime.now(UTC)`. Attach the resolved `AuthorEntity` via `book_author.set_author(author_entity)`. Call `book.set_author(book_author_entity)` for each — this appends and sorts by `display_order` internally.

9. **Persist.** Call `await book_repo.save(book)`. The repository uses `session.merge()` and does NOT commit.

10. **Commit.** Call `await self._db_session.commit()` in the use case, committing all inserts (book row + book-author join rows) in a single transaction.

11. **Return result.** Build and return `CreateBookResult` from the persisted `BookEntity`, resolving the embedded `publisher`, `category`, and `authors` from the entity's selectin-loaded relationships.

---

## Domain Impact

### Entities Involved

| Entity             | Access | Notes                                                        |
| ------------------ | ------ | ------------------------------------------------------------ |
| `BookEntity`       | Write  | Created; aggregate root                                      |
| `BookAuthorEntity` | Write  | Created per author entry; child of BookEntity                |
| `PublisherEntity`  | Read   | Existence check only                                         |
| `CategoryEntity`   | Read   | Existence check only                                         |
| `AuthorEntity`     | Read   | Existence check; resolved and attached to `BookAuthorEntity` |

### Repository Methods Required

| Interface              | Method                                                     | New?                |
| ---------------------- | ---------------------------------------------------------- | ------------------- |
| `IBookRepository`      | `find_by_isbn(isbn: str) -> BookEntity \| None`            | Yes                 |
| `IBookRepository`      | `save(book: BookEntity) -> None`                           | No (existing)       |
| `IPublisherRepository` | `find_by_id(publisher_id: str) -> PublisherEntity \| None` | Yes (new interface) |
| `ICategoryRepository`  | `find_by_id(category_id: str) -> CategoryEntity \| None`   | No (existing)       |
| `IAuthorRepository`    | `find_by_id(author_id: str) -> AuthorEntity \| None`       | No (existing)       |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                                                                                      |
| ---------------------- | --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `CreateBookAuthorItem` | Command (input) | `author_id: str`, `display_order: int`                                                                                                                                      |
| `CreateBookCommand`    | Command (input) | `title`, `price`, `stock_quantity`, `language`, `isbn`, `description`, `page_count`, `published_date`, `publisher_id`, `category_id`, `authors: list[CreateBookAuthorItem]` |
| `CreateBookResult`     | Result (output) | Extends `BaseBookResult` (no additional fields — reuses the existing `BaseBookResult` dataclass from `book_dto.py`)                                                         |

### New Domain Exceptions

| Exception Class          | File                                 | Inherits          |
| ------------------------ | ------------------------------------ | ----------------- |
| `PublisherNotFoundError` | `app/domain/exceptions/publisher.py` | `DomainException` |

### New Error Codes

| Constant              | Value                   | Description                         |
| --------------------- | ----------------------- | ----------------------------------- |
| `PUBLISHER_NOT_FOUND` | `"PUBLISHER_NOT_FOUND"` | Referenced publisher does not exist |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/book-catalog/create-book/`

**`01_success.bru` — Happy Path:**

- [x] Status 201 Created
- [x] `res.body.success` is `true`
- [x] `res.body.data.id` is a string (UUIDv7)
- [x] `res.body.data.title` equals the request title
- [x] `res.body.data.isbn` equals the request ISBN
- [x] `res.body.data.authors` has the correct count and `display_order` values
- [x] `res.body.data.is_active` is `true`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_forbidden_non_admin.bru` — Status 403 when authenticated as `USER` role → `ADMIN_ACCESS_REQUIRED`
- [x] `03_duplicate_isbn.bru` — Status 409 when ISBN already used by another book → `BOOK_ALREADY_EXISTS`
- [x] `04_invalid_isbn.bru` — Status 422 when `isbn` fails checksum → `INVALID_ISBN`
- [x] `05_publisher_not_found.bru` — Status 404 when `publisher_id` does not exist → `PUBLISHER_NOT_FOUND`
- [x] `06_category_not_found.bru` — Status 404 when `category_id` does not exist → `CATEGORY_NOT_FOUND`
- [x] `07_author_not_found.bru` — Status 404 when an `author_id` in `authors` does not exist → `AUTHOR_NOT_FOUND`
- [x] `08_missing_required_fields.bru` — Status 422 when `title`, `price`, `stock_quantity`, or `language` is absent → `UNPROCESSABLE_ENTITY`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_create_book.py`

**Happy Path:**

- [x] `CreateBookUseCase.execute(valid_command)` returns `CreateBookResult` with correct `title`, `price`, `isbn`, and `authors` list
- [x] `CreateBookUseCase.execute(command_without_optional_fields)` returns `CreateBookResult` with `isbn=None`, `publisher=None`, `category=None`, `authors=[]`

**Error Cases:**

- [x] Raises `BookAlreadyExistsError` when a book with the same ISBN already exists
- [x] Raises `PublisherNotFoundError` when `publisher_id` is not found
- [x] Raises `CategoryNotFoundError` when `category_id` is not found
- [x] Raises `AuthorNotFoundError` when any `author_id` is not found

**Edge Cases:**

- [x] `authors` list with duplicate `author_id` entries — only one `BookAuthorEntity` per author (last one wins, matching `set_author` replace semantics)
- [x] `stock_quantity=0` — valid; book is created with no stock and `has_stock=False`
- [x] `authors` with non-sequential `display_order` values (e.g. 1, 3) — stored correctly, sorted in response

---

## Implementation Checklist

- [x] 1. Domain entity — `BookEntity` already exists; no changes needed
- [x] 2. Domain exceptions — `PublisherNotFoundError` in new `app/domain/exceptions/publisher.py`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface methods — add `find_by_isbn` to `IBookRepository`; create new `IPublisherRepository` in `app/domain/repositories/publisher_repository.py` with `find_by_id`
- [x] 4. DTOs — add `CreateBookAuthorItem`, `CreateBookCommand`, `CreateBookResult` to `app/application/dtos/book_dto.py`
- [x] 5. Use case — `app/application/use_cases/book/create_book.py`
- [x] 6. ORM model — `BookModel` already exists; no new table needed
- [x] 7. Mapper — `BookMapper` already exists; no changes needed (author join rows handled by `BookAuthorMapper`)
- [x] 8. Repository implementation — add `find_by_isbn` to `BookRepositoryImpl`; create `PublisherRepositoryImpl` in `app/infrastructure/db/repositories/publisher_repository_impl.py`
- [x] 9. Exception mapping — add `PublisherNotFoundError` to `EXCEPTION_MAP` in `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `PUBLISHER_NOT_FOUND` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `CreateBookRequest` and `CreateBookResponse` to `app/presentation/schemas/book_schema.py`
- [x] 12. Route handler — add `POST /books` to `app/presentation/api/app_api/v1/book_routes.py`
- [x] 13. Wire in `deps.py` — add `get_publisher_repository` provider and `PublisherRepo` typed alias
- [x] 14. Alembic migration — not needed (no schema changes)
- [x] 15. Bruno test files — `bruno/book/create_book/folder.bru` + `01_success.bru` through `08_missing_required_fields.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_create_book.py`
