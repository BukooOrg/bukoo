# User Profile — Get My Shipping Address Proposal

## Overview

| Field        | Value                      |
| ------------ | -------------------------- |
| API Set      | 2. User Profile            |
| Use Case     | 7. Get My Shipping Address |
| File Index   | 02_07                      |
| Access Level | 👤 Customer                |
| Status       | Implemented                |

---

## Endpoint

| Field  | Value                          |
| ------ | ------------------------------ |
| Method | GET                            |
| URL    | `/api/app/v1/users/me/address` |
| Auth   | Bearer token (USER role)       |

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
    "id": "01932abc-...",
    "userId": "01932abc-...",
    "recipientName": "Jane Doe",
    "phone": "+60123456789",
    "addressLine1": "123 Jalan Bukit Bintang",
    "addressLine2": "Level 5",
    "city": "Kuala Lumpur",
    "state": "Wilayah Persekutuan",
    "postcode": "50200",
    "country": "Malaysia",
    "createdAt": "2026-01-15T10:30:00Z",
    "updatedAt": "2026-01-15T10:30:00Z"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code        | Condition                                              |
| ----------- | ----------------- | ------------------------------------------------------ |
| 401         | NOT_AUTH_HEADER   | No Authorization header provided                       |
| 401         | INVALID_TOKEN     | Bearer token is malformed or signature is invalid      |
| 401         | TOKEN_EXPIRED     | Bearer token has expired                               |
| 404         | ADDRESS_NOT_FOUND | The authenticated user has no shipping address on file |

---

## Procedures

1. **Auth guard** — The `CurrentUser` dependency in `deps.py` decodes and validates the Bearer token, checks the revocation blocklist via `RedisCacheService`, and confirms the user is active. If any check fails, FastAPI raises HTTP 401 before reaching the use case.

2. **Invoke use case** — The route handler instantiates `GetMyAddressUseCase` with the resolved `IUserRepository` and `AsyncSession`, then calls `execute(GetMyAddressCommand(user_id=current_user.id))`.

3. **Load user with address** — The use case calls `user_repo.find_by_id(command.user_id)`. Because `UserEntity._address` is `selectin`-loaded, the `AddressEntity` is fetched in the same query without a second round-trip.

4. **User existence guard** — If `find_by_id` returns `None`, raise `UserNotFoundError(command.user_id)`. In practice this cannot happen because `CurrentUser` already confirmed the user is active, but the guard is included for defensive correctness.

5. **Address existence check** — If `user.address` is `None`, raise `AddressNotFoundError(command.user_id)`, which maps to HTTP 404 with error code `ADDRESS_NOT_FOUND`.

6. **Return result** — Build and return `GetMyAddressResult` from the `AddressEntity` fields. No mutation occurs; `commit()` is not called.

---

## Domain Impact

### Entities Involved

| Entity          | Access | Notes                                               |
| --------------- | ------ | --------------------------------------------------- |
| `UserEntity`    | Read   | Selectin-loads `_address` automatically             |
| `AddressEntity` | Read   | Accessed via `user.address`; part of User aggregate |

### Repository Methods Required

| Interface         | Method           | New?          |
| ----------------- | ---------------- | ------------- |
| `IUserRepository` | `find_by_id(id)` | No (existing) |

### New DTOs

| DTO Class             | Type            | Fields                                                                                                                                           |
| --------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `GetMyAddressCommand` | Command (input) | `user_id: str`                                                                                                                                   |
| `GetMyAddressResult`  | Result (output) | `id`, `user_id`, `recipient_name`, `phone`, `address_line1`, `address_line2`, `city`, `state`, `postcode`, `country`, `created_at`, `updated_at` |

### New Domain Exceptions

| Exception Class        | File                               | Inherits          |
| ---------------------- | ---------------------------------- | ----------------- |
| `AddressNotFoundError` | `app/domain/exceptions/address.py` | `DomainException` |

### New Error Codes

| Constant            | Value                 | Description                          |
| ------------------- | --------------------- | ------------------------------------ |
| `ADDRESS_NOT_FOUND` | `"ADDRESS_NOT_FOUND"` | User has no shipping address on file |

---

## Test Cases

### Bruno Tests

**Folder:** `bruno/user_profile/get_my_shipping_address/`

- **`01_success.bru`** — Happy Path:
  - [x] Status 200 OK
  - [x] `res.body.success` is `true`
  - [x] `res.body.data.id` is a string
  - [x] `res.body.data.recipientName` equals the expected value
  - [x] `res.body.data.userId` matches the authenticated user's ID
  - [x] `res.body.meta.requestId` is a string

- **`02_address_not_found.bru`** — Status 404 with error code `ADDRESS_NOT_FOUND` when the user has no address on file

### Pytest Unit Tests

**File:** `backend/tests/unit/test_get_my_address.py`

- **Happy Path:**
  - [x] `GetMyAddressUseCase.execute(valid_query)` returns `GetMyAddressResult` with all correct field values when the user has an address

- **Error Cases:**
  - [x] Raises `UserNotFoundError` when `user_repo.find_by_id` returns `None`
  - [x] Raises `AddressNotFoundError` when `user.address` is `None`

---

## Implementation Checklist

- [x] 1. Domain entity — `AddressEntity` already exists in `app/domain/entities/address_entity.py`
- [x] 2. Domain exceptions — create `app/domain/exceptions/address.py` with `AddressNotFoundError`; export from `app/domain/exceptions/__init__.py`
- [x] 3. Repository interface method(s) — `IUserRepository.find_by_id` already exists; no new methods needed
- [x] 4. DTOs — add `GetMyAddressCommand` and `GetMyAddressResult` to `app/application/dtos/user_dto.py`
- [x] 5. Use case — `app/application/use_cases/user/get_my_address.py`
- [x] 6. ORM model — no new table; `AddressModel` must already exist (verify)
- [x] 7. Mapper — no new mapper; `AddressEntity` is loaded via `UserMapper` (verify)
- [x] 8. Repository implementation — no new repo method needed
- [x] 9. Exception mapping — add `AddressNotFoundError → (404, ErrorCode.ADDRESS_NOT_FOUND)` in `app/presentation/http/exception_mapper.py`
- [x] 10. Error codes — add `ADDRESS_NOT_FOUND = "ADDRESS_NOT_FOUND"` to `app/application/errors/error_codes.py`
- [x] 11. Pydantic schemas — add `AddressResponse` to `app/presentation/schemas/user_schema.py` (or a new `address_schema.py`)
- [x] 12. Route handler — add `GET /me/address` to `app/presentation/api/app_api/v1/user_routes.py`
- [x] 13. Wire in `deps.py` — `IUserRepository` already wired; no additional wiring needed
- [x] 14. Alembic migration — no schema change; skip
- [x] 15. Bruno test files — `bruno/user_profile/get_my_shipping_address/folder.bru` + `01_success.bru` + error case files
- [x] 16. Pytest unit tests — `backend/tests/unit/test_get_my_address.py`
