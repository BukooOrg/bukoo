# Notification API Set — Find Notifications Proposal

## Overview

| Field        | Value                 |
| ------------ | --------------------- |
| API Set      | 13. Notification      |
| Use Case     | 1. Find Notifications |
| File Index   | 13_01                 |
| Access Level | 👤🔑 Both             |
| Status       | Implemented           |

---

## Endpoint

| Field  | Value                       |
| ------ | --------------------------- |
| Method | GET                         |
| URL    | `/api/app/v1/notifications` |
| Auth   | Bearer token (any role)     |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type    | Required | Default | Description                                           |
| --------- | ------- | -------- | ------- | ----------------------------------------------------- |
| page      | integer | No       | 1       | Page number (≥ 1)                                     |
| page_size | integer | No       | 20      | Items per page (1–100)                                |
| sort      | string  | No       | null    | Sort expression e.g. `-created_at`, `created_at`      |
| is_read   | boolean | No       | null    | `true` = read only, `false` = unread only, omit = all |

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
        "id": "019587a2-1234-7abc-8def-000000000001",
        "user_id": "019587a2-1234-7abc-8def-000000000099",
        "type": "payment_success",
        "subject": "Payment Confirmed",
        "body": "Your payment for order BKO-XXXX has been confirmed. Total paid: RM 59.90.",
        "is_read": false,
        "read_at": null,
        "created_at": "2026-01-15T10:29:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total_items": 5,
      "total_pages": 1,
      "has_next": false,
      "has_prev": false
    }
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code           | Condition                                                        |
| ----------- | -------------------- | ---------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID   | Missing, malformed, or revoked Authorization header              |
| 401         | AUTH_TOKEN_EXPIRED   | Bearer token has expired                                         |
| 422         | UNPROCESSABLE_ENTITY | Pydantic validation failure (e.g. `page < 1`, `page_size > 100`) |

---

## Procedures

1. `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the Redis blocklist (`bukoo:blocklist:{jti}`), looks up the user by `sub`, and returns the active `UserEntity`. Returns HTTP 401 on any failure.
2. FastAPI/Pydantic validates the query parameters (`page`, `page_size`, `sort`, `is_read`) against `NotificationListQueryRequest`. HTTP 422 is returned automatically on a constraint violation.
3. The route handler constructs a `FindNotificationsCommand(user_id=current_user.id, query_params=QueryParams(page=PageParams(...), sorts=parse_sort(sort)), is_read=query.is_read)` and calls `FindNotificationsUseCase.execute(cmd)`.
4. The use case calls `notification_repo.find_all(query=cmd.query_params, filters=NotificationFilters(user_id=cmd.user_id, is_read=cmd.is_read))`.
5. The repository executes a paginated `SELECT` on `notifications` filtered by `user_id = :user_id`. If `filters.is_read = True`, it additionally applies `read_at IS NOT NULL`. If `filters.is_read = False`, it applies `read_at IS NULL`. A parallel `COUNT(*)` sub-query (same WHERE predicates, no LIMIT/OFFSET) computes `total_items`. Results default to `ORDER BY created_at DESC` unless overridden by the `sort` parameter.
6. The repository maps each `NotificationModel` to `NotificationEntity` via `NotificationMapper.to_entity()` and returns `PaginatedResult[NotificationEntity]`.
7. The use case constructs `PaginatedResult[NotificationItem]` by mapping each entity to a `NotificationItem` DTO (using `entity.is_read` for the boolean field) and returns it.
8. The route handler maps each `NotificationItem` to `NotificationItemResponse` and wraps the result in `PaginatedResponse[NotificationItemResponse]`.

---

## Domain Impact

### Schema Change Required

> **Note:** The existing `NotificationEntity` and `NotificationModel` track email dispatch state (`status`, `sent_at`) but have no `read_at` field. The `is_read` filter for this endpoint — and the mark-as-read mutations in 13.3 and 13.4 — require adding `_read_at: datetime | None` to the entity and a nullable `read_at` column to the `notifications` table. A new Alembic migration is needed (step 14 in the checklist).
>
> **Design note:** `status` and `sent_at` are email dispatch pipeline fields (PENDING → SENT | FAILED). They are intentionally excluded from the inbox response — the user-facing concern is `is_read` / `read_at`, not whether the Celery worker delivered the email.

### Entities Involved

| Entity               | Access | Notes                    |
| -------------------- | ------ | ------------------------ | ------------------------------------------------------ |
| `NotificationEntity` | Read   | New `\_read_at: datetime | None`field +`is_read: bool` computed property required |

### Repository Methods Required

| Interface                 | Method                                                            | New? |
| ------------------------- | ----------------------------------------------------------------- | ---- |
| `INotificationRepository` | `find_all(query, filters) -> PaginatedResult[NotificationEntity]` | Yes  |

### New DTOs

| DTO Class                  | Type            | Fields                                                                               |
| -------------------------- | --------------- | ------------------------------------------------------------------------------------ |
| `FindNotificationsCommand` | Command (input) | `user_id: str`, `query_params: QueryParams`, `is_read: bool \| None`                 |
| `NotificationItem`         | Result (output) | `id`, `user_id`, `type`, `subject`, `body`, `is_read: bool`, `read_at`, `created_at` |

### New Domain Exceptions

_(None — read-only listing endpoint; no domain invariants are checked)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/13_notification/find_notifications/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.items` is an array
- [x] `res.body.data.pagination.page` equals `1`
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_success_filter_unread.bru` — Status 200 with `?is_read=false`, every item has `is_read = false` and `read_at = null`
- [x] `03_success_filter_read.bru` — Status 200 with `?is_read=true`, every item has `is_read = true` and `read_at != null`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_find_notifications.py`

**Happy Path:**

- [x] `FindNotificationsUseCase.execute(cmd)` with `is_read=None` returns `NotificationItem` entries for all of the user's notifications

**Filter Cases:**

- [x] Returns only notifications where `read_at IS NULL` (i.e. `is_read=False`) when `cmd.is_read=False`
- [x] Returns only notifications where `read_at IS NOT NULL` (i.e. `is_read=True`) when `cmd.is_read=True`

**Edge Cases:**

- [x] Returns `PaginatedResult` with `items=[]` and `total_items=0` when user has no notifications
- [x] Does not return notifications belonging to a different user's `user_id`

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/notification_entity.py`) — add `_read_at: datetime | None` field, `read_at` property, and `is_read: bool` computed property (`return self._read_at is not None`)
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface (`app/domain/repositories/notification_repository.py`) — add `find_all(query, filters) -> PaginatedResult[NotificationEntity]` method; create `NotificationFilters` frozen dataclass (fields: `user_id: str`, `is_read: bool | None`) in the same file
- [x] 4. DTOs (`app/application/dtos/notification_dto.py`) — create `FindNotificationsCommand` and `NotificationItem`
- [x] 5. Use case (`app/application/use_cases/notification/find_notifications.py`)
- [x] 6. ORM model (`app/infrastructure/db/models/notification_model.py`) — add `read_at: Mapped[datetime | None]` nullable `DateTime(timezone=True)` column (default `None`, `init=False`)
- [x] 7. Mapper (`app/infrastructure/db/mappers/notification_mapper.py`) — update `to_entity()` and `to_model()` to include `read_at`
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/notification_repository_impl.py`) — implement `find_all()`
- [x] 9. Exception mapping — none new
- [x] 10. Error codes — none new
- [x] 11. Pydantic schemas (`app/presentation/schemas/notification_schema.py`) — `NotificationListQueryRequest` (extends `ListQueryRequest`, adds `is_read: bool | None = None`) and `NotificationItemResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/notification_routes.py`) — register in `v1/__init__.py`
- [x] 13. Wire in `deps.py` — add `get_notification_repository()` provider and `NotificationRepo = Annotated[INotificationRepository, Depends(get_notification_repository)]`
- [x] 14. Alembic migration — `make migrate msg="add read_at to notifications"` — adds nullable `read_at TIMESTAMPTZ` column; review generated file before applying
- [x] 15. Bruno test files (`bruno/13_notification/find_notifications/` — `folder.bru` + 3 `.bru` files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_find_notifications.py`)
