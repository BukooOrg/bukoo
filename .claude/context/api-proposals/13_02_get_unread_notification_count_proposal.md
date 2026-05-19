# Notification API Set — Get Unread Notification Count Proposal

## Overview

| Field        | Value                            |
| ------------ | -------------------------------- |
| API Set      | 13. Notification                 |
| Use Case     | 2. Get Unread Notification Count |
| File Index   | 13_02                            |
| Access Level | 👤🔑 Both                        |
| Status       | Implemented                      |

---

## Endpoint

| Field  | Value                                    |
| ------ | ---------------------------------------- |
| Method | GET                                      |
| URL    | `/api/app/v1/notifications/unread-count` |
| Auth   | Bearer token (any role)                  |

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
    "unread_count": 3
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code         | Condition                                           |
| ----------- | ------------------ | --------------------------------------------------- |
| 401         | AUTH_TOKEN_INVALID | Missing, malformed, or revoked Authorization header |
| 401         | AUTH_TOKEN_EXPIRED | Bearer token has expired                            |

---

## Procedures

1. `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the Redis blocklist (`bukoo:blocklist:{jti}`), looks up the user by `sub`, and returns the active `UserEntity`. Returns HTTP 401 on any failure.
2. The route handler constructs a `GetUnreadNotificationCountCommand(user_id=current_user.id)` and calls `GetUnreadNotificationCountUseCase.execute(cmd)`.
3. The use case calls `notification_repo.count_unread(user_id=cmd.user_id)`.
4. The repository executes a `SELECT COUNT(*) FROM notifications WHERE user_id = :user_id AND read_at IS NULL AND deleted_at IS NULL` and returns the integer count.
5. The use case returns `GetUnreadNotificationCountResult(unread_count=count)`.
6. The route handler serializes the result as `UnreadNotificationCountResponse(unread_count=result.unread_count)`.

---

## Domain Impact

### Entities Involved

| Entity               | Access | Notes                       |
| -------------------- | ------ | --------------------------- |
| `NotificationEntity` | Read   | Existing; no changes needed |

### Repository Methods Required

| Interface                 | Method                              | New? |
| ------------------------- | ----------------------------------- | ---- |
| `INotificationRepository` | `count_unread(user_id: str) -> int` | Yes  |

### New DTOs

| DTO Class                           | Type            | Fields              |
| ----------------------------------- | --------------- | ------------------- |
| `GetUnreadNotificationCountCommand` | Command (input) | `user_id: str`      |
| `GetUnreadNotificationCountResult`  | Result (output) | `unread_count: int` |

### New Domain Exceptions

_(None)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/notification/get_unread_notification_count/`

**`01_success.bru` — Happy Path:**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.unread_count` is an integer ≥ 0
- [x] `res.body.meta.requestId` is a string

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_unread_notification_count.py`

**Happy Path:**

- [x] `GetUnreadNotificationCountUseCase.execute(cmd)` returns `GetUnreadNotificationCountResult(unread_count=N)` where N matches the number of unread notifications for the user

**Edge Cases:**

- [x] Returns `unread_count=0` when the user has no notifications at all
- [x] Returns `unread_count=0` when all notifications are already read (all have `read_at` set)
- [x] Does not include notifications belonging to a different user's `user_id` in the count

---

## Implementation Checklist

- [x] 1. Domain entity — no changes needed
- [x] 2. Domain exceptions — none new
- [x] 3. Repository interface (`app/domain/repositories/notification_repository.py`) — add `count_unread(user_id: str) -> int` abstract method
- [x] 4. DTOs (`app/application/dtos/notification_dto.py`) — add `GetUnreadNotificationCountCommand` and `GetUnreadNotificationCountResult`
- [x] 5. Use case (`app/application/use_cases/notification/get_unread_notification_count.py`)
- [x] 6. ORM model — no changes needed
- [x] 7. Mapper — no changes needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/notification_repository_impl.py`) — implement `count_unread()`
- [x] 9. Exception mapping — none new
- [x] 10. Error codes — none new
- [x] 11. Pydantic schemas (`app/presentation/schemas/notification_schema.py`) — add `UnreadNotificationCountResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/notification_routes.py`) — add `GET /unread-count` handler; already registered in `v1/__init__.py`
- [x] 13. Wire in `deps.py` — `NotificationRepo` alias already exists from 13.1; no new wiring needed
- [x] 14. Alembic migration — not needed (no schema change)
- [x] 15. Bruno test files (`bruno/notification/get_unread_notification_count/` — `folder.bru` + `01_success.bru`)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_get_unread_notification_count.py`)
