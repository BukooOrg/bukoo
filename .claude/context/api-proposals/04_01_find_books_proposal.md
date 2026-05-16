# 4.1 Find Books — API Proposal

**Status:** Implemented
**API Set:** 4 — Books
**Index:** 4.1

---

## Overview

| Field       | Value                                                            |
| ----------- | ---------------------------------------------------------------- |
| API Set     | 4 — Books                                                        |
| Index       | 4.1                                                              |
| Endpoint    | `GET /books`                                                     |
| Access      | 🌐 Public                                                        |
| Use Case    | `FindBooksUseCase`                                               |
| Description | Paginated, filterable, searchable, sortable list of active books |

---

## Endpoint

```
GET /api/app/v1/books
```

---

## Request — Query Parameters

| Parameter       | Type    | Required | Default       | Validation                         | Notes                                                     |
| --------------- | ------- | -------- | ------------- | ---------------------------------- | --------------------------------------------------------- |
| `page`          | int     | No       | 1             | ≥ 1                                | Pagination page                                           |
| `page_size`     | int     | No       | 20            | 1–100                              | Items per page                                            |
| `sort`          | string  | No       | `-created_at` | comma-separated, prefix `-` = desc | Allowed: `title`, `price`, `created_at`, `published_date` |
| `search`        | string  | No       | —             | max 255 chars                      | FTS on title+description; iLIKE on author name            |
| `category_id`   | string  | No       | —             | —                                  | Exact match on `book.category_id`                         |
| `author_id`     | string  | No       | —             | —                                  | EXISTS join through `books_authors`                       |
| `publisher_id`  | string  | No       | —             | —                                  | Exact match on `book.publisher_id`                        |
| `collection_id` | string  | No       | —             | —                                  | Join: `book → category → collection`                      |
| `language`      | string  | No       | —             | case-insensitive                   | Lowercased before comparison                              |
| `price_min`     | decimal | No       | —             | ≥ 0                                | Inclusive lower bound on price                            |
| `price_max`     | decimal | No       | —             | ≥ 0, ≥ price_min                   | Inclusive upper bound; 422 if < price_min                 |
| `in_stock`      | bool    | No       | —             | —                                  | If `true`: `stock_quantity > 0`                           |

---

## Response

**200 OK**

```json
{
  "items": [
    {
      "id": "01966a23-...",
      "title": "The Midnight Library",
      "price": "14.99",
      "language": "English",
      "cover_url": "https://...",
      "stock_quantity": 42,
      "isbn": "9780525559474",
      "description": "Between life and death...",
      "page_count": 304,
      "published_date": "2020-09-29",
      "is_active": true,
      "publisher": { "id": "...", "name": "Penguin" },
      "category": { "id": "...", "name": "Fiction" },
      "authors": [{ "id": "...", "name": "Matt Haig", "display_order": 1 }],
      "created_at": "2025-05-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 143,
    "total_pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

**422 Unprocessable Entity** — `price_max < price_min`, `page_size > 100`, `page < 1`

---

## Procedures

### Presentation Layer

1. **`BookListQueryRequest`** (`app/presentation/schemas/book_schema.py`)
   - Extends `ListQueryRequest`
   - Adds: `category_id`, `author_id`, `publisher_id`, `collection_id`, `language`, `price_min`, `price_max`, `in_stock`
   - Pydantic `model_validator(mode="after")` raises `ValueError` when `price_max < price_min`
   - `to_command() -> FindBooksCommand` constructs `QueryParams` + `BookFilters`

2. **`find_books` route** (`app/presentation/api/app_api/v1/book_routes.py`)
   - `GET ""` on `APIRouter(prefix="/books", tags=["book"])`
   - Injects `BookRepo`, `DbSession`
   - Instantiates `FindBooksUseCase`, executes with `list_params.to_command()`
   - Maps `BaseBookResult` items → `BookListItemResponse`
   - Returns `PaginatedResponse[BookListItemResponse]`

### Application Layer

3. **`FindBooksCommand`** (`app/application/dtos/book_dto.py`)
   - `@dataclass(frozen=True)`; fields: `query: QueryParams`, `filters: BookFilters`

4. **`BookFilters`** (`app/domain/repositories/book_repository.py`)
   - `@dataclass(frozen=True)` in the domain layer (domain can't import from application)
   - Fields: `search`, `category_id`, `author_id`, `publisher_id`, `collection_id`, `language`, `price_min`, `price_max`, `in_stock`

5. **`BaseBookResult`** + nested (`app/application/dtos/book_dto.py`)
   - `BookPublisherResult`, `BookCategoryResult`, `BookAuthorItemResult`
   - All `@dataclass(frozen=True)`

6. **`FindBooksUseCase`** (`app/application/use_cases/book/find_books.py`)
   - Inherits `BaseUseCase`
   - `execute(cmd: FindBooksCommand) -> PaginatedResult[BaseBookResult]`
   - Calls `self._book_repo.find_all(cmd.query, cmd.filters)`
   - Maps `BookEntity` → `BaseBookResult` via `_to_result(book)`

### Domain Layer

7. **`IBookRepository`** (`app/domain/repositories/book_repository.py`)
   - ABC; `find_all(query: QueryParams, filters: BookFilters) -> PaginatedResult[BookEntity]`
   - `find_by_id(book_id: str) -> BookEntity | None`
   - `save(book: BookEntity) -> None`

### Infrastructure Layer

8. **`BookRepositoryImpl`** (`app/infrastructure/db/repositories/book_repository_impl.py`)
   - `SORTABLE_FIELDS`: `title`, `price`, `published_date`, `created_at`, `updated_at`
   - Base conditions: `deleted_at IS NULL AND deactivated_at IS NULL`
   - **FTS:** `search_vector @@ plainto_tsquery('english', :q) OR EXISTS(author iLIKE)`
   - **`collection_id`:** LEFT JOIN `CategoryModel` on `book.category_id = category.id`
   - **`author_id`:** EXISTS subquery on `books_authors`
   - Relationship loading: `selectinload(publisher)`, `selectinload(category)`, `selectinload(author_associations).selectinload(author)`
   - Default sort: `created_at DESC`

---

## Domain Impact

**Entity changes:** None — `BookEntity` already exposes all needed fields.

**New repository interface:**

- `IBookRepository.find_all(query: QueryParams, filters: BookFilters) -> PaginatedResult[BookEntity]`

**New DTOs:** `FindBooksCommand`, `BaseBookResult`, `BookPublisherResult`, `BookCategoryResult`, `BookAuthorItemResult`

**New domain value object:** `BookFilters` (in `domain/repositories/book_repository.py`)

**New exceptions:** None — empty result is valid.

**New error codes:** None.

**DB schema change:** `search_vector tsvector GENERATED ALWAYS AS (...) STORED` + GIN index on `books`.

---

## Test Cases

### Bruno (HTTP)

```
GET /api/app/v1/books                              → 200, items[], pagination meta
GET /api/app/v1/books?search=harry                 → 200, FTS results
GET /api/app/v1/books?search=rowling               → 200, author name match
GET /api/app/v1/books?category_id=<id>             → 200, filtered by category
GET /api/app/v1/books?author_id=<id>               → 200, filtered by author
GET /api/app/v1/books?publisher_id=<id>            → 200, filtered by publisher
GET /api/app/v1/books?collection_id=<id>           → 200, filtered via category join
GET /api/app/v1/books?language=English             → 200, case-insensitive match
GET /api/app/v1/books?price_min=10&price_max=20    → 200, price range
GET /api/app/v1/books?in_stock=true                → 200, only stock_quantity > 0
GET /api/app/v1/books?sort=price                   → 200, sorted by price ASC
GET /api/app/v1/books?sort=-title                  → 200, sorted by title DESC
GET /api/app/v1/books?page=2&page_size=5           → 200, correct pagination meta
GET /api/app/v1/books?price_min=50&price_max=10    → 422, invalid price range
GET /api/app/v1/books?page_size=101                → 422, exceeds maximum
```

### Pytest Unit (`tests/unit/use_cases/test_find_books.py`)

- `test_returns_empty_paginated_result_when_no_books`
- `test_returns_paginated_books`
- `test_applies_search_filter_via_repo`
- `test_applies_category_filter_via_repo`
- `test_applies_in_stock_filter_via_repo`
- `test_maps_entity_fields_to_base_book_result`
- `test_maps_publisher_to_result`
- `test_maps_category_to_result`
- `test_maps_authors_to_result`

### Pytest Integration (`tests/integration/repositories/test_book_repository.py`)

- `test_find_all_returns_only_active_non_deleted_books`
- `test_find_all_fts_matches_title`
- `test_find_all_fts_matches_author_name`
- `test_find_all_filter_by_category_id`
- `test_find_all_filter_by_author_id`
- `test_find_all_filter_by_publisher_id`
- `test_find_all_filter_by_collection_id`
- `test_find_all_filter_by_language_case_insensitive`
- `test_find_all_filter_by_price_range`
- `test_find_all_filter_in_stock`
- `test_find_all_sort_by_price_asc`
- `test_find_all_sort_by_title_desc`
- `test_find_all_default_sort_created_at_desc`
- `test_find_all_pagination`

---

## Implementation Checklist

- [x] Add `search: str | None = None` to `QueryParams` in `backend/app/core/query_params.py`
- [x] Add `search` to `ListQueryRequest` and `to_query_params()` in `backend/app/presentation/schemas/list_schema.py`
- [x] Alembic migration: `search_vector` generated tsvector column + GIN index on `books`
- [x] Add `Computed` `search_vector` column + GIN index to `BookModel`
- [x] Create `backend/app/domain/repositories/book_repository.py` — `BookFilters`, `IBookRepository`
- [x] Export `BookFilters`, `IBookRepository` from `backend/app/domain/repositories/__init__.py`
- [x] Create `backend/app/application/dtos/book_dto.py` — `FindBooksCommand`, `BaseBookResult`, nested results
- [x] Create `backend/app/application/use_cases/book/find_books.py` — `FindBooksUseCase`
- [x] Create `backend/app/infrastructure/db/repositories/book_repository_impl.py` — `BookRepositoryImpl`
- [x] Export `BookRepositoryImpl` from `backend/app/infrastructure/db/repositories/__init__.py`
- [x] Create `backend/app/presentation/schemas/book_schema.py` — `BookListQueryRequest`, `BookListItemResponse`, nested responses
- [x] Create `backend/app/presentation/api/app_api/v1/book_routes.py` — `find_books` route
- [x] Add `get_book_repository`, `BookRepo` to `backend/app/presentation/dependencies/deps.py`
- [x] Register `book_router` in `backend/app/presentation/api/app_api/v1/__init__.py`
- [x] Run `make upgrade` — apply migration
- [x] Run `make be-check` — ruff + mypy must pass
- [x] Write Bruno test collection for book endpoints
- [x] Write pytest unit tests for `FindBooksUseCase`
- [ ] Write pytest integration tests for `BookRepositoryImpl`
