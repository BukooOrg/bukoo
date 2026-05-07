# User Profile — Upsert Shipping Address Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 2. User Profile            |
| Use Case     | 8. Upsert Shipping Address |
| File Index   | 02_08                      |
| Access Level | 👤 Customer                |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                          |
| ------ | ------------------------------ |
| Method | PUT                            |
| URL    | `/api/app/v1/users/me/address` |
| Auth   | Bearer token (USER role)       |

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

| Field          | Type           | Required | Constraints        |
| -------------- | -------------- | -------- | ------------------ |
| recipient_name | string         | Yes      | 2–255 characters   |
| phone          | string         | Yes      | 5–30 characters    |
| address_line1  | string         | Yes      | 1–255 characters   |
| address_line2  | string \| null | No       | Max 255 characters |
| city           | string         | Yes      | 1–100 characters   |
| state          | string         | Yes      | 1–100 characters   |
| postcode       | string         | Yes      | 1–20 characters    |
| country        | string         | Yes      | 1–100 characters   |

**Example:**

```json
{
  "recipient_name": "Jane Doe",
  "phone": "+60123456789",
  "address_line1": "12 Jalan Bukit Bintang",
  "address_line2": "Unit 5A",
  "city": "Kuala Lumpur",
  "state": "Wilayah Persekutuan",
  "postcode": "55100",
  "country": "Malaysia"
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
    "id": "01932abc-0000-7000-a000-000000000001",
    "user_id": "01932abc-0000-7000-a000-000000000002",
    "recipient_name": "Jane Doe",
    "phone": "+60123456789",
    "address_line1": "12 Jalan Bukit Bintang",
    "address_line2": "Unit 5A",
    "city": "Kuala Lumpur",
    "state": "Wilayah Persekutuan",
    "postcode": "55100",
    "country": "Malaysia",
    "created_at": "2026-01-15T10:00:00Z",
    "updated_at": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code             | Condition                           |
| ----------- | ---------------------- | ----------------------------------- |
| 401         | `AUTH_TOKEN_INVALID`   | Missing, expired, or revoked token  |
| 403         | `FORBIDDEN`            | Token belongs to an ADMIN-role user |
| 422         | `UNPROCESSABLE_ENTITY` | Pydantic validation failure on body |

---

## Procedures

1. **Auth guard** — `CurrentUser` dependency in `deps.py` validates the Bearer token, checks the blocklist, and confirms the user is active with `USER` role. Any token failure raises HTTP 401. An ADMIN-role token is rejected with HTTP 403 (this endpoint is `👤 Customer` only).

2. **Input validation** — FastAPI/Pydantic validates the request body against `UpsertAddressRequest`. Returns HTTP 422 with field-level errors on failure.

3. **Load user with address** — Call `await user_repo.find_by_id(current_user.id)`. Since `UserEntity._address` is selectin-loaded, the result includes the existing `AddressEntity` (or `None`). Because the user is authenticated, `None` here is theoretically impossible, but raise `UserNotFoundError` defensively.

4. **Branch — create vs update:**
   - If `user.address is None`: construct a new `AddressEntity(_id=str(uuid7()), _user_id=user.id, _recipient_name=..., _phone=..., _address_line1=..., _address_line2=..., _city=..., _state=..., _postcode=..., _country=..., _created_at=datetime.now(UTC), _updated_at=datetime.now(UTC))`.
   - If `user.address is not None`: call `user.address.update(recipient_name=..., phone=..., address_line1=..., address_line2=..., city=..., state=..., postcode=..., country=...)`. The `update()` method on `AddressEntity` replaces all mutable fields and stamps `_updated_at`.

5. **Persist** — Call `await address_repo.save(address_entity)`. The repository uses `session.merge(model)` to handle both insert and update without needing to know which branch was taken. Repository does NOT commit.

6. **Commit** — Call `await self._db_session.commit()`.

7. **Return** — Build and return `UpsertAddressResult` from the (new or updated) `AddressEntity`.

---

## Domain Impact

### Entities Involved

| Entity          | Access       | Notes                                             |
| --------------- | ------------ | ------------------------------------------------- |
| `UserEntity`    | Read         | Loaded to obtain existing `_address`; not mutated |
| `AddressEntity` | Read / Write | Created or updated in-place via `update()` method |

### Repository Methods Required

| Interface            | Method                         | New?                |
| -------------------- | ------------------------------ | ------------------- |
| `IUserRepository`    | `find_by_id(user_id)`          | No (existing)       |
| `IAddressRepository` | `save(address: AddressEntity)` | Yes (new interface) |

### New DTOs

| DTO Class              | Type            | Fields                                                                                                                                           |
| ---------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `UpsertAddressCommand` | Command (input) | `user_id`, `recipient_name`, `phone`, `address_line1`, `address_line2`, `city`, `state`, `postcode`, `country`                                   |
| `UpsertAddressResult`  | Result (output) | `id`, `user_id`, `recipient_name`, `phone`, `address_line1`, `address_line2`, `city`, `state`, `postcode`, `country`, `created_at`, `updated_at` |

### New Domain Exceptions

_(None — `UserNotFoundError` from `app/domain/exceptions/auth.py` covers the defensive guard in step 3)_

### New Error Codes

_(None)_

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/User Profile/Upsert Shipping Address/`

Each test case is a separate `.bru` file.

**`01_success_create.bru` — Happy Path (no existing address):**

- [x] Status 200 OK
- [x] `res.body.success` is `true`
- [x] `res.body.data.recipient_name` equals `"Jane Doe"`
- [x] `res.body.data.user_id` equals the authenticated user's ID
- [x] `res.body.data.id` is a non-empty string
- [x] `res.body.meta.requestId` is a string

**`02_success_update.bru` — Happy Path (address already exists):**

- [x] Status 200 OK
- [x] `res.body.data.recipient_name` reflects the new value
- [x] `res.body.data.created_at` is unchanged from the first upsert
- [x] `res.body.data.updated_at` is later than `created_at`

**Error Cases:**

- [x] `03_validation_missing_required.bru` — Status 422 when required fields (`recipient_name`, `address_line1`, etc.) are absent
- [x] `04_validation_empty_string.bru` — Status 422 when required string fields are empty

### Pytest Unit Tests

**File:** `backend/tests/unit/test_upsert_address.py`

**Happy Path:**

- [x] `UpsertAddressUseCase.execute(command)` returns `UpsertAddressResult` with all correct fields when user has no existing address (create branch)
- [x] `UpsertAddressUseCase.execute(command)` returns `UpsertAddressResult` with updated fields when user has an existing address (update branch)
- [x] After the update branch, `result.created_at` matches the original address `created_at`

**Error Cases:**

- [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`

**Edge Cases:**

- [x] `address_line2=None` is accepted and persisted as `None`
- [x] Calling upsert twice with different data returns the latest values on the second call

---

## Implementation Checklist

- [x] 1. Domain entity (`app/domain/entities/address_entity.py`) — existing (`AddressEntity` with `update()` method already present)
- [x] 2. Domain exceptions (`app/domain/exceptions/`) — no new exceptions needed
- [x] 3. Repository interface (`app/domain/repositories/address_repository.py`) — **New** `IAddressRepository` with `save(address: AddressEntity) -> None`
- [x] 4. DTOs (`app/application/dtos/user_dto.py`) — add `UpsertAddressCommand` and `UpsertAddressResult`
- [x] 5. Use case (`app/application/use_cases/user/upsert_address.py`) — **New** `UpsertAddressUseCase`
- [x] 6. ORM model — existing `AddressModel` confirmed; no new table needed
- [x] 7. Mapper — existing `AddressMapper` confirmed; no new mapper needed
- [x] 8. Repository implementation (`app/infrastructure/db/repositories/address_repository_impl.py`) — **New** `AddressRepositoryImpl` with `save` using `session.merge()`
- [x] 9. Exception mapping (`app/presentation/http/exception_mapper.py`) — no new entries needed
- [x] 10. Error codes (`app/application/errors/error_codes.py`) — no new entries needed
- [x] 11. Pydantic schemas (`app/presentation/schemas/user_schema.py`) — add `UpsertAddressRequest` and `AddressResponse`
- [x] 12. Route handler (`app/presentation/api/app_api/v1/user_routes.py`) — add `PUT /me/address` handler
- [x] 13. Wire in `deps.py` — add `get_address_repository` / `AddressRepo` and `require_customer` / `CustomerUser`
- [x] 14. Alembic migration — skipped; `addresses` table exists in `create_all_tables` migration
- [x] 15. Bruno test files (`bruno/user_profile/upsert_shipping_address/` — `folder.bru` + 6 test files)
- [x] 16. Pytest unit tests (`backend/tests/unit/test_upsert_address.py`)
