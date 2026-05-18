# Admin — User Management — Find Users Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 3. Admin — User Management |
| Use Case     | 1. Find Users              |
| File Index   | 03_01                      |
| Access Level | 🔑 Admin                   |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                     |
| ------ | ------------------------- |
| Method | GET                       |
| URL    | `/api/app/v1/users`       |
| Auth   | Bearer token (ADMIN role) |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter   | Type    | Required | Default       | Description                                                                                                                        |
| ----------- | ------- | -------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| `page`      | integer | No       | `1`           | Page number (≥ 1)                                                                                                                  |
| `page_size` | integer | No       | `20`          | Items per page (1–100)                                                                                                             |
| `sort`      | string  | No       | `-created_at` | Comma-separated sort fields. Prefix `-` for descending. Allowed: `full_name`, `email`, `created_at`, `updated_at`, `last_login_at` |
| `search`    | string  | No       | —             | Case-insensitive substring match against `full_name` or `email`                                                                    |
| `role`      | string  | No       | —             | Filter by `UserRole`: `admin` or `user`                                                                                            |
| `status`    | string  | No       | —             | Filter by `UserStatus`: `pending`, `active`, or `suspended`                                                                        |

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
    "items": [
      {
        "id": "01932abc-0000-7000-0000-000000000001",
        "email": "jane@example.com",
        "full_name": "Jane Doe",
        "date_of_birth": "1990-05-15",
        "role": "user",
        "status": "active",
        "avatar_url": "https://cdn.example.com/avatars/jane.jpg",
        "have_password": true,
        "last_login_at": "2026-05-17T08:30:00Z",
        "created_at": "2026-01-10T12:00:00Z",
        "updated_at": "2026-05-17T08:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 150,
      "total_pages": 8,
      "has_next": true,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-05-18T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code             | Condition                                                                |
| ----------- | ---------------------- | ------------------------------------------------------------------------ |
| 401         | `AUTH_TOKEN_INVALID`   | Missing, expired, or revoked Bearer token                                |
| 403         | `PERMISSION_DENIED`    | Authenticated user does not have the `admin` role                        |
| 422         | `UNPROCESSABLE_ENTITY` | Pydantic validation failure (e.g. invalid `role` enum value, `page` < 1) |

---

## Procedures

1. **Auth/guard** — The `AdminUser` dependency in `deps.py` validates the Bearer token via `JWTService`, checks the blocklist via `RedisCacheService`, loads the user via `IUserRepository.find_by_id`, and asserts `user.role == UserRole.ADMIN`; raises HTTP 401/403 if any check fails. The use case is not involved in auth.

2. **Input validation** — FastAPI resolves `FindUsersQueryRequest` (a `ListQueryRequest` subclass) via `Depends`. Pydantic validates `page ≥ 1`, `page_size` in 1–100, and the `role`/`status` enum values; returns HTTP 422 on failure.

3. **Invoke use case** — The route handler instantiates `FindUsersUseCase(db_session=db_session, user_repo=user_repo)` and calls `await use_case.execute(cmd)`, where `cmd` is a `FindUsersCommand` built from the validated query params.

4. **Build filter and query objects** — `FindUsersUseCase.execute` constructs a `UserFilters(role=cmd.role, status=cmd.status)` and passes `cmd.query_params` (a `QueryParams` with `PageParams` and `list[SortOrder]`) together to `IUserRepository.find_all(query=cmd.query_params, filters=user_filters)`.

5. **Repository executes paginated query** — `UserRepositoryImpl.find_all` builds a `WHERE` clause starting with `UserModel.deleted_at.is_(None)`. If `filters.role` is set, appends `UserModel.role == filters.role`. If `filters.status` is set, appends `UserModel.status == filters.status`. If `query.search` is set, appends `or_(UserModel.full_name.ilike(f"%{search}%"), UserModel.email.ilike(f"%{search}%"))`.

6. **Count total** — The repository executes `SELECT count(*) FROM (base_stmt WHERE clause)` as a subquery to compute `total_items` for pagination metadata.

7. **Apply sort** — `SORTABLE_FIELDS` maps string names to `UserModel` columns (`full_name`, `email`, `created_at`, `updated_at`, `last_login_at`). For each `SortOrder` in `query.sorts` whose `field` is in `SORTABLE_FIELDS`, append the appropriate `.asc()` / `.desc()` clause. If no valid sort clauses remain, default to `UserModel.created_at.desc()`.

8. **Apply pagination** — Append `.offset(query.page.offset).limit(query.page.limit)` and execute. Map each `UserModel` to `UserEntity` via `UserMapper.to_entity`.

9. **Return** — `FindUsersUseCase.execute` wraps the results in a `PaginatedResult[FindUserResult]`, building one `FindUserResult` per entity. No `commit()` is called (read-only).

10. **Route handler maps to response** — The handler builds a `PaginatedResponse[UserListItemResponse]` using `PaginationMeta.from_result(result)` and returns it; `ResponseFormatterMiddleware` wraps it in the standard envelope.

---

## Domain Impact

### Entities Involved

| Entity       | Access | Notes                       |
| ------------ | ------ | --------------------------- |
| `UserEntity` | Read   | Soft-deleted users excluded |

### Repository Methods Required

| Interface         | Method                                                                              | New? |
| ----------------- | ----------------------------------------------------------------------------------- | ---- |
| `IUserRepository` | `find_all(query: QueryParams, filters: UserFilters) -> PaginatedResult[UserEntity]` | Yes  |

### New DTOs

| DTO Class          | Type            | Fields                                                                                                                                    |
| ------------------ | --------------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| `FindUsersCommand` | Command (input) | `query_params: QueryParams`, `role: UserRole \| None`, `status: UserStatus \| None`                                                       |
| `FindUserResult`   | Result (output) | `id`, `email`, `full_name`, `date_of_birth`, `role`, `status`, `avatar_url`, `have_password`, `last_login_at`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — no domain rules are enforced on a read-only list query.)_

### New Error Codes

_(None — existing `AUTH_TOKEN_INVALID` and `PERMISSION_DENIED` codes cover all error cases.)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user-management/find-users/`

Each test case is a separate `.bru` file.

**`01_success.bru` — Happy Path (no filters):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] `res.body.data.pagination.page` equals `1`
- [x] `res.body.data.pagination.total_items` is an integer ≥ 0
- [x] `res.body.meta.requestId` is a string

**`02_filter_by_role.bru` — Filter `role=admin`:**

- [x] Status 200 OK
- [x] All `res.body.data.items[*].role` equal `"admin"`

**`03_filter_by_status.bru` — Filter `status=suspended`:**

- [x] Status 200 OK
- [x] All `res.body.data.items[*].status` equal `"suspended"`

**`04_search.bru` — Search by name/email fragment:**

- [x] Status 200 OK
- [x] All returned items have `full_name` or `email` containing the search term (case-insensitive)

**`05_sort.bru` — Sort `full_name` ascending:**

- [x] Status 200 OK
- [x] `res.body.data.items` is ordered by `full_name` ascending

**`06_pagination.bru` — `page=2&page_size=5`:**

- [x] Status 200 OK
- [x] `res.body.data.items.length` ≤ 5
- [x] `res.body.data.pagination.page` equals `2`

**`07_invalid_role_param.bru` — `role=unknown`:**

- [x] Status 422

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_users.py`

**Happy Path:**

- [x] `FindUsersUseCase.execute(FindUsersCommand(query_params=..., role=None, status=None))` returns `PaginatedResult[FindUserResult]` with `items` matching all non-deleted users from the fake repo
- [x] Result `pagination` metadata (`total_items`, `page`, `page_size`) matches injected fake data

**Filter Cases:**

- [x] `role=UserRole.ADMIN` — only admin users are returned
- [x] `status=UserStatus.SUSPENDED` — only suspended users are returned
- [x] `role=UserRole.USER, status=UserStatus.ACTIVE` — both filters applied together

**Search:**

- [x] `search="jane"` — returns only users whose `full_name` or `email` contains `"jane"` (case-insensitive, tested in fake repo)

**Edge Cases:**

- [x] Empty repository — returns `PaginatedResult` with `items=[]`, `total_items=0`
- [x] `page=2` when total items < `page_size` — returns empty `items` list with correct pagination meta

---

## Implementation Checklist

- [x] 1. Domain entity — `UserEntity` existing; no changes needed
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface — add `UserFilters` dataclass + `find_all` method to `app/domain/repositories/user_repository.py`
- [x] 4. DTOs — add `FindUsersCommand` and `FindUserResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case — `app/application/use_cases/user/find_users.py` + export in `app/application/use_cases/user/__init__.py`
- [x] 6. ORM model — no new table; `UserModel` exists
- [x] 7. Mapper — `UserMapper` exists; no changes needed
- [x] 8. Repository implementation — add `find_all` to `app/infrastructure/db/repositories/user_repository_impl.py`
- [x] 9. Exception mapping — no new exceptions
- [x] 10. Error codes — no new codes
- [x] 11. Pydantic schemas — add `FindUsersQueryRequest` and `UserListItemResponse` to `app/presentation/schemas/user_schema.py`
- [x] 12. Route handler — add `GET /` handler `find_users` to `app/presentation/api/app_api/v1/user_routes.py`
- [x] 13. Wire in `deps.py` — `UserRepo` alias already exists; no new wiring needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files — `folder.bru` + `01_success.bru` through `07_invalid_role_param.bru`
- [x] 16. Pytest unit tests — `backend/tests/unit/test_find_users.py`
