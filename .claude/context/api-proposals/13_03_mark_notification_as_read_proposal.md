# Notification API Set — Mark Notification As Read Proposal

## Overview

| Field        | Value                        |
| ------------ | ---------------------------- |
| API Set      | 13. Notification             |
| Use Case     | 3. Mark Notification As Read |
| File Index   | 13_03                        |
| Access Level | 👤🔑 Both                    |
| Status       | Implemented                  |

---

## Endpoint

| Field  | Value                                              |
| ------ | -------------------------------------------------- |
| Method | PATCH                                              |
| URL    | `/api/app/v1/notifications/{notification_id}/read` |
| Auth   | Bearer token (any role)                            |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter       | Type          | Description                         |
| --------------- | ------------- | ----------------------------------- |
| notification_id | string (UUID) | ID of the notification to mark read |

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
    "id": "019587a2-1234-7abc-8def-000000000001",
    "user_id": "019587a2-1234-7abc-8def-000000000099",
    "type": "payment_success",
    "subject": "Payment Confirmed",
    "body": "Your payment for order BKO-XXXX has been confirmed.",
    "is_read": true,
    "read_at": "2026-01-15T10:30:00Z",
    "created_at": "2026-01-15T10:29:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code             | Condition                                                               |
| ----------- | ---------------------- | ----------------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID     | Missing, malformed, or revoked Authorization header                     |
| 401         | AUTH_TOKEN_EXPIRED     | Bearer token has expired                                                |
| 404         | NOTIFICATION_NOT_FOUND | Notification does not exist, or belongs to a different user (USER role) |

---

## Procedures

1. `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the Redis blocklist (`bukoo:blocklist:{jti}`), looks up the user by `sub`, and returns the active `UserEntity`. Returns HTTP 401 on any failure.
2. The route handler constructs a `MarkNotificationAsReadCommand(notification_id=notification_id, user_id=current_user.id, is_admin=current_user.role == UserRole.ADMIN)` and calls `MarkNotificationAsReadUseCase.execute(cmd)`.
3. The use case calls `notification_repo.find_by_id(cmd.notification_id)`. If the result is `None`, it raises `NotificationNotFoundError(notification_id)`.
4. If `cmd.is_admin` is `False` and `notification.user_id != cmd.user_id`, the use case raises `NotificationNotFoundError(notification_id)` — this deliberately treats unauthorized access as "not found" to avoid revealing the existence of other users' notifications.
5. If the notification is already read (`notification.is_read` is `True`), the use case returns the existing notification item immediately without mutation, persist, or commit (idempotent).
6. The use case calls `notification.mark_read()`, which sets `_read_at = datetime.now(UTC)`.
7. The use case calls `notification_repo.save(notification)`.
8. The use case calls `await self._db_session.commit()`.
9. The use case maps the updated entity to a `NotificationItem` DTO and returns it.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                        |
| -------------------- | ------ | ------------------------------------------------------------ |
| `NotificationEntity` | Write  | New `mark_read()` method sets `_read_at = datetime.now(UTC)` |

### Repository Methods Required

| Interface                 | Method                                                           | New? |
| ------------------------- | ---------------------------------------------------------------- | ---- |
| `INotificationRepository` | `find_by_id(notification_id: str) -> NotificationEntity \| None` | Yes  |

### New DTOs

| DTO Class                       | Type            | Fields                                                   |
| ------------------------------- | --------------- | -------------------------------------------------------- |
| `MarkNotificationAsReadCommand` | Command (input) | `notification_id: str`, `user_id: str`, `is_admin: bool` |

Result reuses existing `NotificationItem` DTO.

### New Domain Exceptions

| Exception Class             | File                                    | Inherits          |
| --------------------------- | --------------------------------------- | ----------------- |
| `NotificationNotFoundError` | `app/domain/exceptions/notification.py` | `DomainException` |

### New Error Codes

| Constant                 | Value                      | Description                             |
| ------------------------ | -------------------------- | --------------------------------------- |
| `NOTIFICATION_NOT_FOUND` | `"NOTIFICATION_NOT_FOUND"` | Notification not found or access denied |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/notification/mark_notification_as_read/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.is_read` is `true`
- [x] `res.body.data.read_at` is a non-null string
- [x] `res.body.meta.requestId` is a string

**`02_admin_success.bru` — Happy Path**

- with `user_id` query param

### Pytest Unit Testsx

**File:** `backend/tests/unit/test_mark_notification_as_read.py`

**Happy Path:**

- [x] `MarkNotificationAsReadUseCase.execute(cmd)` returns `NotificationItem` with `is_read=True` and `read_at` set when notification is unread
- [x] Returns the notification unchanged when it is already read (idempotent — no commit called)

**Error Cases:**

- [x] Raises `NotificationNotFoundError` when no notification exists with the given ID
- [x] Raises `NotificationNotFoundError` when the notification belongs to a different user and `is_admin=False`

**Edge Cases:**

- [x] Admin (`is_admin=True`) can mark a notification belonging to another user as read
- [x] `db_session.commit` is called exactly once on a successful mutation and not called on an already-read notification

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/notification_entity.py`) — add `mark_read()` method
- [x] 2. Domain exceptions (`app/domain/exceptions/notification.py`) — create new file with `NotificationNotFoundError`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/notification_repository.py`) — add `find_by_id(notification_id: str) -> NotificationEntity | None` abstract method
- [x] 4. DTOs (`app/application/dtos/notification_dto.py`) — add `MarkNotificationAsReadCommand`
- [x] 5. Use case (`app/application/use_cases/notification/mark_notification_as_read.py`)
- [x] 6. ORM model — no changes needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/notification_repository_impl.py`) — implement `find_by_id()`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `NotificationNotFoundError → HTTP 404, NOTIFICATION_NOT_FOUND`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `NOTIFICATION_NOT_FOUND`
- [x] 11. Pydantic schemas (`app/presentation/schemas/notification_schema.py`) — add `MarkNotificationAsReadResponse` (same shape as `NotificationItemResponse`)
- [x] 12. Route handler (`app/presentation/api/app_api/v1/notification_routes.py`) — add `PATCH /{notification_id}/read` handler
- [x] 13. Wire in `deps.py` — `NotificationRepo` already exists; no new wiring needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/notification/mark_notification_as_read/` — `folder.bru` + `01_success.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_mark_notification_as_read.py`)
