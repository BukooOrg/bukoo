# RESTful API Design Best Practices

> This document defines the RESTful API standards for this project. All API endpoints must conform to the guidelines below to ensure consistency, maintainability, and a predictable developer experience.

---

## Table of Contents

- [RESTful API Design Best Practices](#restful-api-design-best-practices)
  - [Table of Contents](#table-of-contents)
  - [1. Consistent Response Envelope](#1-consistent-response-envelope)
    - [Success Response](#success-response)
    - [Error Response](#error-response)
  - [2. HTTP Status Codes](#2-http-status-codes)
    - [2xx — Success](#2xx--success)
    - [4xx — Client Errors](#4xx--client-errors)
    - [5xx — Server Errors](#5xx--server-errors)
  - [3. Naming Conventions — camelCase Keys](#3-naming-conventions--camelcase-keys)
  - [4. Date \& Time Formatting](#4-date--time-formatting)
  - [5. API Versioning](#5-api-versioning)
  - [6. Filtering and Sorting](#6-filtering-and-sorting)
  - [7. Pagination](#7-pagination)
    - [Option A — Offset-Based Pagination](#option-a--offset-based-pagination)
    - [Option B — Cursor-Based Pagination](#option-b--cursor-based-pagination)
    - [Option C — Page-Based Pagination](#option-c--page-based-pagination)
  - [8. Embedding Related Resources](#8-embedding-related-resources)
  - [9. Null vs. Missing Fields](#9-null-vs-missing-fields)
  - [10. Rate Limiting](#10-rate-limiting)
  - [11. Response Compression](#11-response-compression)
  - [12. Security Essentials](#12-security-essentials)

---

## 1. Consistent Response Envelope

Every API response **must** follow the same top-level shape. A uniform envelope allows clients to write generic error handling and parsing logic without special-casing individual endpoints.

### Success Response

```json
{
  "success": true,
  "data": {
    "id": 42,
    "name": "Jane Doe",
    "email": "jane@example.com"
  },
  "meta": {
    "requestId": "req_abc123",
    "timestamp": "2026-02-25T10:30:00Z"
  }
}
```

### Error Response

Use the same envelope structure, replacing `data` with an `error` object.

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Email is required",
    "details": [{ "field": "email", "message": "must not be empty" }]
  },
  "meta": {
    "requestId": "req_def456",
    "timestamp": "2026-02-25T10:30:01Z"
  }
}
```

For validation errors with multiple fields:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": [
      {
        "field": "name",
        "message": "Name is required",
        "code": "REQUIRED_FIELD"
      },
      {
        "field": "photoUrls",
        "message": "At least one photo URL is required",
        "code": "REQUIRED_FIELD"
      }
    ]
  },
  "meta": {
    "requestId": "req_ghi789",
    "timestamp": "2026-02-25T10:30:02Z"
  }
}
```

---

## 2. HTTP Status Codes

Return the most semantically appropriate status code. Never return `200 OK` for an error.

### 2xx — Success

| Code  | Name            | When to use                                                 |
| ----- | --------------- | ----------------------------------------------------------- |
| `200` | OK              | Standard successful response (GET, PUT, PATCH)              |
| `201` | Created         | A new resource was successfully created (POST)              |
| `202` | Accepted        | Request received and queued; processing is not yet complete |
| `204` | No Content      | Successful request with no response body (e.g., DELETE)     |
| `206` | Partial Content | A range request was fulfilled (e.g., chunked downloads)     |

### 4xx — Client Errors

| Code  | Name                   | When to use                                                        |
| ----- | ---------------------- | ------------------------------------------------------------------ |
| `400` | Bad Request            | Malformed request syntax, invalid parameters, or corrupted payload |
| `401` | Unauthorized           | Missing or invalid authentication credentials                      |
| `403` | Forbidden              | Authenticated, but lacking permission for the resource             |
| `404` | Not Found              | The requested resource does not exist                              |
| `405` | Method Not Allowed     | HTTP method is not supported for this endpoint                     |
| `408` | Request Timeout        | Server timed out waiting for the client                            |
| `409` | Conflict               | State conflict (e.g., duplicate resource, optimistic lock failure) |
| `410` | Gone                   | Resource permanently deleted (permanent 404)                       |
| `413` | Payload Too Large      | Request body exceeds the size limit                                |
| `415` | Unsupported Media Type | Content-Type is not supported (e.g., expected `application/json`)  |
| `422` | Unprocessable Entity   | Well-formed request but fails semantic/business validation         |
| `429` | Too Many Requests      | Client has exceeded the rate limit                                 |

### 5xx — Server Errors

| Code  | Name                  | When to use                                            |
| ----- | --------------------- | ------------------------------------------------------ |
| `500` | Internal Server Error | Unexpected server-side failure                         |
| `501` | Not Implemented       | Endpoint or feature is not yet supported               |
| `502` | Bad Gateway           | Upstream service returned an invalid response          |
| `503` | Service Unavailable   | Server temporarily unavailable (maintenance, overload) |
| `504` | Gateway Timeout       | Upstream service did not respond in time               |

---

## 3. Naming Conventions — camelCase Keys

All JSON response keys **must** use `camelCase`. JavaScript is the primary consumer of most JSON APIs and uses camelCase natively. Other casing styles force clients to transform every response before use.

```json
// ✅ Good
{
  "firstName": "Jane",
  "lastName": "Doe",
  "createdAt": "2026-01-15T09:00:00Z"
}

// ❌ Avoid
{
  "first_name": "Jane",
  "last_name": "Doe",
  "created_at": "2026-01-15T09:00:00Z"
}
```

---

## 4. Date & Time Formatting

Always return dates and timestamps in **ISO 8601 format** with an explicit timezone. Unix timestamps are ambiguous (seconds vs. milliseconds) and locale-formatted strings are unparseable.

```json
// ✅ Good — unambiguous, parseable everywhere
{ "createdAt": "2026-02-25T10:30:00Z" }

// ❌ Bad — seconds or milliseconds?
{ "createdAt": 1772130600 }

// ❌ Bad — locale-dependent, unparseable
{ "createdAt": "Feb 25, 2026 10:30 AM" }
```

---

## 5. API Versioning

APIs evolve. When making breaking changes, increment the version so existing clients remain unaffected. Use **URL path versioning** as the standard approach.

```
GET /api/v1/users/42
GET /api/v2/users/42
```

- Increment the version only for **breaking changes** (field removal, type changes, behaviour changes).
- Non-breaking additions (new optional fields, new endpoints) do **not** require a new version.
- Maintain at least one previous major version and deprecate with advance notice.

---

## 6. Filtering and Sorting

Never force clients to download entire collections and filter client-side. Expose query parameters for common operations.

```
# Filter by a field
GET /api/v1/orders?status=shipped

# Sort ascending
GET /api/v1/orders?sort=createdAt

# Sort descending (minus prefix convention)
GET /api/v1/orders?sort=-createdAt

# Combine filter and sort
GET /api/v1/orders?status=shipped&sort=-createdAt
```

> The `-` prefix for descending sort (e.g., `-createdAt`) is a widely adopted convention. All supported filter fields and sort keys must be documented.

---

## 7. Pagination

All list endpoints that could return more than a small, bounded number of records **must** support pagination. Choose the strategy that best fits the use case.

### Option A — Offset-Based Pagination

Simple and intuitive. Best for small, stable datasets. Can produce duplicates or gaps when items are added or removed between pages.

**Request:**

```
GET /api/v1/pets?limit=20&offset=40
```

**Response:**

```json
{
  "success": true,
  "data": [
    { "id": 41, "name": "Buddy", "status": "available" },
    { "id": 42, "name": "Luna", "status": "pending" }
  ],
  "pagination": {
    "limit": 20,
    "offset": 40,
    "totalItems": 1000,
    "hasNext": true,
    "hasPrev": true
  }
}
```

### Option B — Cursor-Based Pagination

Stable and performant for large or frequently-mutating datasets. The cursor is an opaque token — clients pass it back verbatim; they do not need to parse it.

**Request:**

```
GET /api/v1/pets?limit=20&cursor=eyJpZCI6NDB9
```

**Response:**

```json
{
  "success": true,
  "data": [
    { "id": 41, "name": "Buddy", "status": "available" },
    { "id": 42, "name": "Luna", "status": "pending" }
  ],
  "pagination": {
    "limit": 20,
    "nextCursor": "eyJpZCI6MTI0fQ==",
    "prevCursor": "eyJpZCI6MTIzfQ==",
    "hasNext": true,
    "hasPrev": false
  }
}
```

### Option C — Page-Based Pagination

Most intuitive for UIs that display page numbers. Shares the same consistency drawbacks as offset-based pagination.

**Request:**

```
GET /api/v1/pets?page=3&perPage=20
```

**Response:**

```json
{
  "success": true,
  "data": [],
  "pagination": {
    "page": 3,
    "perPage": 20,
    "totalPages": 15,
    "totalItems": 300,
    "hasNext": true,
    "hasPrev": true
  }
}
```

---

## 8. Embedding Related Resources

Support optional embedding of related resources to reduce client round trips, especially for mobile clients where latency is critical.

**Without embedding** _(requires a second request for related data)_:

```
GET /api/v1/pets/10
```

```json
{
  "id": 10,
  "name": "Max",
  "categoryId": 1
}
```

**With embedding** _(related resource included in one response)_:

```
GET /api/v1/pets/10?embed=category
```

```json
{
  "id": 10,
  "name": "Max",
  "category": {
    "id": 1,
    "name": "Dogs"
  }
}
```

> Use the `embed` query parameter to opt in. Never embed by default if the payload is large — embedding should be explicit.

---

## 9. Null vs. Missing Fields

There is a semantic difference between a field that is `null` and a field that is absent. Be deliberate and consistent.

**Field is `null`** — the field exists on the resource but has no value:

```json
{
  "id": 10,
  "name": "Max",
  "description": null
}
```

**Field is absent** — the field does not apply to this resource, or was not requested (e.g., sparse fieldsets):

```json
{
  "id": 10,
  "name": "Max"
}
```

> Do not use `null` to mean "not applicable". Omit the field entirely if the concept does not apply to the resource.

---

## 10. Rate Limiting

Include rate limit metadata in response headers so clients can throttle proactively rather than waiting for a `429` error.

```
HTTP/1.1 200 OK
X-RateLimit-Limit:     100
X-RateLimit-Remaining: 73
X-RateLimit-Reset:     1772131200
```

| Header                  | Description                                      |
| ----------------------- | ------------------------------------------------ |
| `X-RateLimit-Limit`     | Maximum number of requests allowed in the window |
| `X-RateLimit-Remaining` | Requests remaining in the current window         |
| `X-RateLimit-Reset`     | Unix timestamp when the window resets            |

When a client exceeds the limit, respond with `429 Too Many Requests` and include a `Retry-After` header:

```
HTTP/1.1 429 Too Many Requests
Retry-After: 30
```

---

## 11. Response Compression

Enable gzip compression for all text-based responses to significantly reduce bandwidth consumption.

**Request:**

```
GET /api/v1/pets
Accept-Encoding: gzip, deflate
```

**Response headers:**

```
Content-Encoding: gzip
Content-Length: 1234
```

**Compression rules:**

| Condition                                          | Action                         |
| -------------------------------------------------- | ------------------------------ |
| Response body > 1 KB                               | Always compress                |
| Response body < 500 bytes                          | Skip — overhead not worthwhile |
| Already-compressed formats (images, video, binary) | Skip                           |

Most HTTP clients handle decompression transparently. Compression typically reduces JSON response sizes by **70–90%**.

---

## 12. Security Essentials

JSON APIs are a common attack surface. The following rules are mandatory for all endpoints.

| Rule                            | Details                                                                        |
| ------------------------------- | ------------------------------------------------------------------------------ |
| **Always use HTTPS**            | Never transmit credentials or tokens over plain HTTP                           |
| **Validate all input**          | Reject unexpected fields, enforce types, and set maximum lengths               |
| **Avoid exposing internal IDs** | Use UUIDs or slugs instead of auto-incrementing database primary keys          |
| **Set proper CORS headers**     | Never use `Access-Control-Allow-Origin: *` in production                       |
| **Use short-lived JWTs**        | Follow JWT best practices; keep token expiry short and implement refresh flows |
