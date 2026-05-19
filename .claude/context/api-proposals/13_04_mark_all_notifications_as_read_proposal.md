# Notification API Set — Mark All Notifications As Read Proposal

## Overview

| Field        | Value                             |
| ------------ | --------------------------------- |
| API Set      | 13. Notification                  |
| Use Case     | 4. Mark All Notifications As Read |
| File Index   | 13_04                             |
| Access Level | 👤🔑 Both                         |
| Status       | Implemented                       |

---

## Endpoint

| Field  | Value                                |
| ------ | ------------------------------------ |
| Method | PATCH                                |
| URL    | `/api/app/v1/notifications/read-all` |
| Auth   | Bearer token (any role)              |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

_(None)_

### Query Parameters

| Parameter | Type          | Required | Default | Description                                                                     |
| --------- | ------------- | -------- | ------- | ------------------------------------------------------------------------------- |
| user_id   | string (UUID) | No       | —       | Admin only: mark all unread notifications for this user. Ignored for USER role. |

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
    "marked_count": 5
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

> `marked_count` is the number of previously-unread notifications transitioned to read. Returns `0` when all notifications were already read (idempotent).

### Error Responses

| HTTP Status | Error Code         | Condition                                                       |
| ----------- | ------------------ | --------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID | Missing, malformed, or revoked Authorization header             |
| 401         | AUTH_TOKEN_EXPIRED | Bearer token has expired                                        |
| 403         | PERMISSION_DENIED  | Non-admin caller supplied `?user_id=`                           |
| 404         | USER_NOT_FOUND     | Admin supplied `?user_id=` that does not correspond to any user |

---

## Procedures

1. `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the Redis blocklist (`bukoo:blocklist:{jti}`), looks up the user by `sub`, and returns the active `UserEntity`. Returns HTTP 401 on any failure.
2. The route handler constructs a `MarkAllNotificationsAsReadCommand(user_id=current_user.id, is_admin=current_user.role == UserRole.ADMIN, target_user_id=query_user_id)` and calls `MarkAllNotificationsAsReadUseCase.execute(cmd)`.
3. If `cmd.target_user_id` is not `None` and `cmd.is_admin` is `False`, the use case raises `AdminRoleRequiredError`.
4. If `cmd.target_user_id` is not `None` and `cmd.is_admin` is `True`, the use case calls `user_repo.find_by_id(cmd.target_user_id)`. If the result is `None`, it raises `UserNotFoundError(cmd.target_user_id)`.
5. The use case resolves `effective_user_id = cmd.target_user_id if cmd.target_user_id else cmd.user_id`.
6. The use case calls `notification_repo.mark_all_as_read_user_id(user_id=effective_user_id)`. This executes a single bulk SQL `UPDATE` against the `notifications` table, setting `is_read = true`, `read_at = NOW()`, and `updated_at = NOW()` for all rows where `user_id = effective_user_id AND is_read = false AND deleted_at IS NULL`. The method returns the number of rows affected as `marked_count: int`. If there are no unread notifications, `marked_count` is `0`.
7. The use case calls `await self._db_session.commit()`.
8. The use case returns `MarkAllNotificationsAsReadResult(marked_count=marked_count)`.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                                             |
| -------------------- | ------ | --------------------------------------------------------------------------------- |
| `NotificationEntity` | Write  | Bulk-mutated via repository; entity `mark_read()` method is not called per-record |
| `UserEntity`         | Read   | Existence check when admin provides `?user_id=`                                   |

### Repository Methods Required

| Interface                 | Method                                          | New?          |
| ------------------------- | ----------------------------------------------- | ------------- |
| `INotificationRepository` | `mark_all_as_read_user_id(user_id: str) -> int` | Yes           |
| `IUserRepository`         | `find_by_id(user_id: str)`                      | No (existing) |

### New DTOs

| DTO Class                           | Type            | Fields                                                          |
| ----------------------------------- | --------------- | --------------------------------------------------------------- |
| `MarkAllNotificationsAsReadCommand` | Command (input) | `user_id: str`, `is_admin: bool`, `target_user_id: str \| None` |
| `MarkAllNotificationsAsReadResult`  | Result (output) | `marked_count: int`                                             |

### New Domain Exceptions

| Exception Class          | File                              | Inherits          |
| ------------------------ | --------------------------------- | ----------------- |
| `AdminRoleRequiredError` | `app/domain/exceptions/common.py` | `DomainException` |

### New Error Codes

| Constant            | Value                 | Description                                           |
| ------------------- | --------------------- | ----------------------------------------------------- |
| `PERMISSION_DENIED` | `"PERMISSION_DENIED"` | Caller lacks the required role to perform this action |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/notification/mark_all_notifications_as_read/`

**`01_success.bru` — Happy Path (own notifications):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.marked_count` is a non-negative integer
- [x] `res.body.meta.requestId` is a string

**Error Cases:**

- [x] `02_admin_user_not_found.bru` — Status 404 when admin provides a non-existent `?user_id=` → error code `USER_NOT_FOUND`
- [x] `03_idempotent.bru` — Status 200 with `marked_count: 0` when all notifications are already read

### Pytest Unit Tests

**File:** `backend/tests/unit/test_mark_all_notifications_as_read.py`

**Happy Path:**

- [x] `MarkAllNotificationsAsReadUseCase.execute(cmd)` returns `MarkAllNotificationsAsReadResult` with correct `marked_count` when called for the current user
- [x] Admin with `target_user_id` set returns correct `marked_count` for the target user
- [x] `db_session.commit` is called exactly once in both cases

**Error Cases:**

- [x] Raises `AdminRoleRequiredError` when `is_admin=False` and `target_user_id` is provided
- [x] Raises `UserNotFoundError` when `is_admin=True` and `target_user_id` does not resolve to any user

**Edge Cases:**

- [x] Returns `marked_count: 0` when no unread notifications exist for the target user (idempotent — commit is still called)
- [x] Admin without `?user_id=` marks only their own notifications (not all users')

---

## Implementation Checklist

- [x] 1. Domain entity — no changes needed
- [x] 2. Domain exceptions (`app/domain/exceptions/common.py`) — create new file with `AdminRoleRequiredError`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface (`app/domain/repositories/notification_repository.py`) — add `mark_all_as_read_user_id(user_id: str) -> int` abstract method
- [x] 4. DTOs (`app/application/dtos/notification_dto.py`) — add `MarkAllNotificationsAsReadCommand` and `MarkAllNotificationsAsReadResult`
- [x] 5. Use case (`app/application/use_cases/notification/mark_all_notifications_as_read.py`) — inject both `INotificationRepository` and `IUserRepository`
- [x] 6. ORM model — no changes needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/notification_repository_impl.py`) — implement `mark_all_as_read_user_id()` using a bulk SQL `UPDATE` with `rowcount`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — add `AdminRoleRequiredError → HTTP 403, PERMISSION_DENIED`
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — add `PERMISSION_DENIED`
- [x] 11. Pydantic schemas (`app/presentation/schemas/notification_schema.py`) — add `MarkAllNotificationsAsReadResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/notification_routes.py`) — add `PATCH /read-all` handler with optional `user_id: str | None = Query(None)`
- [x] 13. Wire in `deps.py` — `NotificationRepo` and `UserRepo` already exist; no new wiring needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/notification/04_mark_all_notifications_as_read/` — `folder.bru` + 3 test files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_mark_all_notifications_as_read.py`)
