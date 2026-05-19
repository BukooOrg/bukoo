# Notification API Set — Delete Notification Proposal

## Overview

| Field        | Value                  |
| ------------ | ---------------------- |
| API Set      | 13. Notification       |
| Use Case     | 5. Delete Notification |
| File Index   | 13_05                  |
| Access Level | 👤🔑 Both              |
| Status       | Implemented            |

---

## Endpoint

| Field  | Value                                         |
| ------ | --------------------------------------------- |
| Method | DELETE                                        |
| URL    | `/api/app/v1/notifications/{notification_id}` |
| Auth   | Bearer token (any role)                       |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Authorization | Yes      | Bearer {access_token} |

### Path Parameters

| Parameter       | Type          | Description                      |
| --------------- | ------------- | -------------------------------- |
| notification_id | string (UUID) | ID of the notification to delete |

### Query Parameters

_(None)_

### Request Body

_(None)_

---

## Response

### Success Response

**Status:** 204 No Content

_(Empty body — `ResponseFormatterMiddleware` passes non-JSON responses through unchanged.)_

### Error Responses

| HTTP Status | Error Code             | Condition                                                               |
| ----------- | ---------------------- | ----------------------------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID     | Missing, malformed, or revoked Authorization header                     |
| 401         | AUTH_TOKEN_EXPIRED     | Bearer token has expired                                                |
| 404         | NOTIFICATION_NOT_FOUND | Notification does not exist, or belongs to a different user (USER role) |

---

## Procedures

1. `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the Redis blocklist (`bukoo:blocklist:{jti}`), looks up the user by `sub`, and returns the active `UserEntity`. Returns HTTP 401 on any failure.
2. The route handler constructs a `DeleteNotificationCommand(notification_id=notification_id, user_id=current_user.id, is_admin=current_user.role == UserRole.ADMIN)` and calls `DeleteNotificationUseCase.execute(cmd)`.
3. The use case calls `notification_repo.find_by_id(cmd.notification_id)`. If the result is `None`, it raises `NotificationNotFoundError(cmd.notification_id)`.
4. If `cmd.is_admin` is `False` and `notification.user_id != cmd.user_id`, the use case raises `NotificationNotFoundError(cmd.notification_id)` — this deliberately treats unauthorized access as "not found" to avoid revealing the existence of other users' notifications.
5. The use case calls `notification_repo.delete(cmd.notification_id)`. This executes a hard `DELETE FROM notifications WHERE id = :notification_id` — the `NotificationModel` has no `deleted_at` by design, so there is no soft-delete path.
6. The use case calls `await self._db_session.commit()`.
7. The use case returns `None`. The route handler returns `Response(status_code=204)`.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                                                                            |
| -------------------- | ------ | -------------------------------------------------------------------------------- |
| `NotificationEntity` | Read   | Loaded only for ownership check; no mutation — hard delete bypasses entity state |

### Repository Methods Required

| Interface                 | Method                                                           | New?          |
| ------------------------- | ---------------------------------------------------------------- | ------------- |
| `INotificationRepository` | `find_by_id(notification_id: str) -> NotificationEntity \| None` | No (existing) |
| `INotificationRepository` | `delete(notification_id: str) -> None`                           | Yes           |

### New DTOs

| DTO Class                   | Type            | Fields                                                   |
| --------------------------- | --------------- | -------------------------------------------------------- |
| `DeleteNotificationCommand` | Command (input) | `notification_id: str`, `user_id: str`, `is_admin: bool` |

_(No result DTO — use case returns `None`; route returns 204.)_

### New Domain Exceptions

_(None — `NotificationNotFoundError` already exists from 13.3)_

### New Error Codes

_(None — `NOTIFICATION_NOT_FOUND` already exists from 13.3)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/notification/delete_notification/`

**`01_success.bru` — Happy Path:**

- [x] Status 204 No Content
- [x] Response body is empty

**Error Cases:**

- [x] `02_not_found.bru` — Status 404 when notification ID does not exist → error code `NOTIFICATION_NOT_FOUND`
- [x] `03_wrong_owner.bru` — Status 404 when USER role targets a notification belonging to a different user → error code `NOTIFICATION_NOT_FOUND`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_delete_notification.py`

**Happy Path:**

- [x] `DeleteNotificationUseCase.execute(cmd)` returns `None` and calls `notification_repo.delete` with the correct `notification_id`
- [x] Admin can delete a notification belonging to another user
- [x] `db_session.commit` is called exactly once on success

**Error Cases:**

- [x] Raises `NotificationNotFoundError` when no notification exists with the given ID
- [x] Raises `NotificationNotFoundError` when `is_admin=False` and the notification belongs to a different user

**Edge Cases:**

- [x] `notification_repo.delete` is NOT called when the existence/ownership check fails
- [x] Admin without `is_admin=False` cannot delete another user's notification (ownership guard enforced)

---

## Implementation Checklist

- [x] 1. Domain entity — no changes needed (`NotificationModel` uses hard delete; no `soft_delete()` method required)
- [x] 2. Domain exceptions — no changes needed (`NotificationNotFoundError` already exists)
- [x] 3. Repository interface (`app/domain/repositories/notification_repository.py`) — add `delete(notification_id: str) -> None` abstract method
- [x] 4. DTOs (`app/application/dtos/notification_dto.py`) — add `DeleteNotificationCommand`
- [x] 5. Use case (`app/application/use_cases/notification/delete_notification.py`)
- [x] 6. ORM model — no changes needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/notification_repository_impl.py`) — implement `delete()` with a hard `DELETE` SQL statement
- [x] 9. Exception mapping — no changes needed
- [x] 10. Error codes — no changes needed
- [x] 11. Pydantic schemas — no new schema needed (204 response has no body)
- [x] 12. Route handler (`app/presentation/api/app_api/v1/notification_routes.py`) — add `DELETE /{notification_id}` handler; use `response_class=Response, status_code=204`
- [x] 13. Wire in `deps.py` — `NotificationRepo` already exists; no new wiring needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/notification/05_delete_notification/` — `folder.bru` + one file per test case above)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_delete_notification.py`)
