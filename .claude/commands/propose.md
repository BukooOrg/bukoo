# /propose — API Endpoint Proposal Generator

Generates a detailed API endpoint proposal for a Bukoo use case, iterates with the developer until approved, then saves it to `.claude/context/api-proposals/`.

## Input Format

```
/propose <endpoint_ref>
```

Accepted formats for `<endpoint_ref>`:

- Catalog notation: `1.6`, `4.3`, `11.1`
- Zero-padded: `01_06`, `04_03`
- Description: `auth logout`, `create book`, `place order`

---

## Steps

### 1. Parse the Reference

Map the input to an API set index and endpoint index using `.claude/context/api-endpoint-catalog.md`. If the reference is ambiguous or not found, list the closest matches and ask the user to clarify.

### 2. Read Context (in parallel)

- `.claude/context/api-endpoint-catalog.md` — endpoint spec and notes
- `.claude/context/architecture.md` — layer rules, request lifecycle, patterns
- `.claude/context/domain-model.md` — entities, invariants, existing repo interfaces

### 3. Generate the Proposal

Using the **Proposal Template** below, produce a complete proposal covering all 8 sections. The Procedures section requires the highest effort — it must be detailed enough that any developer could implement the endpoint without ambiguity.

### 4. Output in Chat

Present the full proposal as a fenced markdown block. Then ask:

> "Does this proposal look correct? Let me know any sections to revise, or say **approved** when ready to save."

### 5. Iterate

Incorporate all feedback and re-output the updated proposal. Repeat until the user signals final approval with any of: `approved`, `looks good`, `save it`, `save`, `lgtm`.

### 6. Save

Save the final proposal to:

```
.claude/context/api-proposals/[api_set_idx]_[uc_idx]_[use_case_name]_proposal.md
```

- Both indices zero-padded to 2 digits
- Use case name: lowercase with underscores, no spaces or hyphens
- Set the status field to `Approved`

Confirm the saved path to the user.

---

## Proposal Template

````markdown
# [API Set Name] — [Use Case Name] Proposal

## Overview

| Field        | Value                                            |
| ------------ | ------------------------------------------------ |
| API Set      | [index]. [name]                                  |
| Use Case     | [local index]. [name]                            |
| File Index   | [api_set_idx]\_[uc_idx]                          |
| Access Level | [🌐 Public / 👤 Customer / 🔑 Admin / 👤🔑 Both] |
| Status       | Draft                                            |

---

## Endpoint

| Field  | Value                                                                                   |
| ------ | --------------------------------------------------------------------------------------- |
| Method | [GET / POST / PATCH / PUT / DELETE]                                                     |
| URL    | `/api/app/v1/[path]`                                                                    |
| Auth   | [None / Bearer token (USER role) / Bearer token (ADMIN role) / Bearer token (any role)] |

---

## Request

### Headers

| Header        | Required | Description           |
| ------------- | -------- | --------------------- |
| Content-Type  | [Yes/No] | application/json      |
| Authorization | [Yes/No] | Bearer {access_token} |

### Path Parameters

| Parameter | Type          | Description   |
| --------- | ------------- | ------------- |
| [param]   | string (UUID) | [description] |

_(None — if no path params)_

### Query Parameters

| Parameter | Type   | Required | Default   | Description   |
| --------- | ------ | -------- | --------- | ------------- |
| [param]   | [type] | [Yes/No] | [default] | [description] |

_(None — if no query params)_

### Request Body

| Field   | Type   | Required | Constraints   |
| ------- | ------ | -------- | ------------- |
| [field] | [type] | [Yes/No] | [constraints] |

_(None — if no request body)_

**Example:**

```json
{
  "field": "value"
}
```
````

---

## Response

### Success Response

**Status:** [HTTP status code and name]

```json
{
  "success": true,
  "data": {
    "field": "value"
  },
  "meta": {
    "requestId": "01932abc-...",
    "timestamp": "2026-01-15T10:30:00Z"
  }
}
```

### Error Responses

| HTTP Status | Error Code                 | Condition                   |
| ----------- | -------------------------- | --------------------------- |
| 400         | VALIDATION_ERROR           | [condition]                 |
| 401         | AUTH_TOKEN_INVALID         | [condition]                 |
| 403         | PERMISSION_DENIED          | [condition]                 |
| 404         | [RESOURCE]\_NOT_FOUND      | [condition]                 |
| 409         | [RESOURCE]\_ALREADY_EXISTS | [condition]                 |
| 422         | UNPROCESSABLE_ENTITY       | Pydantic validation failure |

---

## Procedures

Detailed step-by-step logic (pseudocode in English). Be specific: name exact exception classes, error codes, field names, and where `commit()` is called. Short and concise without missing details.

1. [Auth/Guard check] Validate Bearer token via `CurrentUser` / `AdminUser` dependency. If invalid → raise HTTP 401 (handled by deps.py, not the use case).
2. [Input validation] Pydantic schema validates the request body. If invalid → raise HTTP 422 (handled automatically by FastAPI).
3. [Business logic step] ...
4. [Repository call] Call `repo.find_by_id(id)`. If not found → raise `[EntityNotFoundError]`.
5. [Domain rule enforcement] Check invariant. If violated → raise `[DomainException]`.
6. [Mutation] Call entity method (e.g., `entity.update(...)`). This updates `_updated_at` internally.
7. [Persist] Call `repo.save(entity)`. Repository does NOT commit.
8. [Commit] Call `await self._db_session.commit()` in the use case.
9. [Side effect] (If applicable) Dispatch Celery task / upload to storage / send email.
10. [Return] Build and return the result DTO.

---

## Domain Impact

### Entities Involved

| Entity       | Access       | Notes   |
| ------------ | ------------ | ------- |
| [EntityName] | Read / Write | [notes] |

### Repository Methods Required

| Interface           | Method              | New?          |
| ------------------- | ------------------- | ------------- |
| `I[Name]Repository` | `find_by_id(id)`    | No (existing) |
| `I[Name]Repository` | `[new_method](...)` | Yes           |

### New DTOs

| DTO Class       | Type            | Fields   |
| --------------- | --------------- | -------- |
| `[Name]Command` | Command (input) | [fields] |
| `[Name]Result`  | Result (output) | [fields] |

_(None — if reusing existing DTOs)_

### New Domain Exceptions

| Exception Class | File                               | Inherits          |
| --------------- | ---------------------------------- | ----------------- |
| `[Name]Error`   | `app/domain/exceptions/[group].py` | `DomainException` |

_(None — if no new exceptions needed)_

### New Error Codes

| Constant | Value      | Description   |
| -------- | ---------- | ------------- |
| `[NAME]` | `"[NAME]"` | [description] |

_(None — if no new error codes needed)_

---

## Test Cases

### Bruno Tests

**File:** `bruno/[api_set_folder]/[use_case_name].bru`

**Happy Path:**

- [ ] Status [200/201] OK
- [ ] `res.body.success` is `true`
- [ ] `res.body.data.[field]` equals expected value
- [ ] `res.body.meta.requestId` is a string

**Error Cases:**

- [ ] Status 401 when no Authorization header provided
- [ ] Status 401 when token is expired or invalid
- [ ] Status [4xx] when [condition] → error code `[CODE]`
- [ ] Status [4xx] when [condition] → error code `[CODE]`

### Pytest Unit Tests

**File:** `backend/tests/unit/test_[use_case_name].py`

**Happy Path:**

- [ ] `[UseCaseName].execute(valid_command)` returns `[ResultDTO]` with correct field values

**Error Cases:**

- [ ] Raises `[DomainException]` when [condition]
- [ ] Raises `[DomainException]` when [condition]

**Edge Cases:**

- [ ] [boundary or duplicate scenario]
- [ ] [empty or null input scenario]

---

## Implementation Checklist

- [ ] 1. Domain entity (`app/domain/entities/`) — _new or existing_
- [ ] 2. Domain exceptions (`app/domain/exceptions/`) — _new or existing_
- [ ] 3. Repository interface method(s) (`app/domain/repositories/`)
- [ ] 4. DTOs / service interfaces (`app/application/dtos/`, `app/application/interfaces/`)
- [ ] 5. Use case (`app/application/use_cases/[group]/[action].py`)
- [ ] 6. ORM model (`app/infrastructure/db/models/`) — _if new table_
- [ ] 7. Mapper (`app/infrastructure/db/mappers/`) — _if new model_
- [ ] 8. Repository implementation (`app/infrastructure/db/repositories/`)
- [ ] 9. Exception mapping (`app/presentation/http/exception_mapper.py`)
- [ ] 10. Error codes (`app/application/errors/error_codes.py`)
- [ ] 11. Pydantic schemas (`app/presentation/schemas/`)
- [ ] 12. Route handler (`app/presentation/api/app_api/v1/[group]_routes.py`)
- [ ] 13. Wire in `deps.py` (`app/presentation/dependencies/deps.py`)
- [ ] 14. Alembic migration — _only if schema changed_ (`make migrate msg="..."`)
- [ ] 15. Bruno test file (`bruno/[api_set]/[use_case].bru`)
- [ ] 16. Pytest unit tests (`backend/tests/unit/test_[use_case].py`)

```

---

## Error Handling

- **Endpoint not found**: List the top 3 closest matches from the catalog and ask the user to confirm.
- **Ambiguous input** (e.g., `delete` matches multiple endpoints): Show all matching endpoints and ask the user to pick.
- **Save conflict** (file already exists): Ask the user whether to overwrite or create a new revision.
```
