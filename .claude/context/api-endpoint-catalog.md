# Bukoo Backend — API Endpoint Catalog

## Context

This catalog defines the complete set of REST API endpoints for the Bukoo
bookstore platform, derived from the feature list in `.claude/context/project-context.md`.
It serves as the implementation roadmap: each item is one API endpoint (= one
use case to build). Existing auth endpoints (`POST /auth/register`,
`POST /auth/login`, `POST /auth/login/google`) are marked for **reimplementation**
— current versions were scaffolded for early setup only.

## Design Decisions

| Decision                    | Choice                                                    | Rationale                                                                   |
| --------------------------- | --------------------------------------------------------- | --------------------------------------------------------------------------- |
| URL prefix                  | `/api/app/v1/...` for all endpoints                       | Single prefix; access control via RBAC, not URL separation                  |
| Auth/RBAC                   | JWT Bearer token; role guard (`USER` / `ADMIN`) per route | Consistent with existing token service                                      |
| Password reset              | Email-based OTP/token flow                                | Standard and secure; avoids storing security-question answers               |
| Email verification          | Required post-registration (PENDING → ACTIVE)             | `UserStatus.PENDING` already modelled in domain                             |
| Report generation           | Async Celery job (submit → poll → download)               | Reports scan large datasets; sync would timeout; Celery already provisioned |
| Admin vs customer endpoints | Same resource paths, RBAC-differentiated                  | REST best practice; avoids duplicated route modules                         |

## Access Level Legend

| Symbol | Meaning                               |
| ------ | ------------------------------------- |
| 🌐     | Public — no authentication required   |
| 👤     | Customer — authenticated, `USER` role |
| 🔑     | Admin — authenticated, `ADMIN` role   |
| 👤🔑   | Both authenticated roles              |

---

## API Set Catalog

---

### 1. Auth API Set

> Reimplements existing scaffold endpoints. Covers account creation, verification,
> credential and OAuth login (provider authorization URL + server-side callback), logout,
> and password recovery.

| #    | Endpoint                          | Method | Access | Notes                                                                                                                                                                            |
| ---- | --------------------------------- | ------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1.1  | `/auth/register`                  | POST   | 🌐     | Create customer account; triggers verification email; status = PENDING. **Reimplemented.**                                                                                       |
| 1.2  | `/auth/verify-email`              | POST   | 🌐     | Verify email with OTP/token; transitions status PENDING → ACTIVE                                                                                                                 |
| 1.3  | `/auth/resend-verification`       | POST   | 🌐     | Resend verification email to unverified address                                                                                                                                  |
| 1.4  | `/auth/login`                     | POST   | 🌐     | Credential login (email + password); returns JWT. **Reimplemented.**                                                                                                             |
| 1.5a | `/auth/oauth/{provider}/login`    | GET    | 🌐     | Returns the authorization URL for the given OAuth provider as JSON; frontend redirects browser to it. Generates a CSRF state token stored in Redis (TTL 10 min).                 |
| 1.5b | `/auth/oauth/{provider}/callback` | GET    | 🌐     | OAuth callback from provider; verifies CSRF state, exchanges code, finds or creates user, sets auth cookie, and redirects to frontend. All errors redirect with `?error=` param. |
| 1.6  | `/auth/logout`                    | POST   | 👤🔑   | Invalidate / revoke current session token                                                                                                                                        |
| 1.7  | `/auth/password/forgot`           | POST   | 🌐     | Send password reset OTP/token to registered email                                                                                                                                |
| 1.8  | `/auth/password/reset/verify`     | GET    | 🌐     | Validate reset token is still valid (frontend UX: show reset form only if valid)                                                                                                 |
| 1.9  | `/auth/password/reset`            | POST   | 🌐     | Submit new password with valid reset token; token invalidated after use                                                                                                          |

---

### 2. User Profile API Set

> Self-service account management for the authenticated user (customer or admin).

| #   | Endpoint             | Method | Access | Notes                                               |
| --- | -------------------- | ------ | ------ | --------------------------------------------------- |
| 2.1 | `/users/me`          | GET    | 👤🔑   | Get own profile                                     |
| 2.2 | `/users/me`          | PATCH  | 👤🔑   | Update own profile (full name, date of birth, etc.) |
| 2.3 | `/users/me`          | DELETE | 👤     | Soft-delete own account and personal data           |
| 2.4 | `/users/me/avatar`   | POST   | 👤🔑   | Upload profile picture (multipart) to MinIO/S3      |
| 2.5 | `/users/me/avatar`   | DELETE | 👤🔑   | Remove profile picture                              |
| 2.6 | `/users/me/password` | PATCH  | 👤🔑   | Change password (requires current password)         |
| 2.7 | `/users/me/address`  | GET    | 👤     | Get shipping address                                |
| 2.8 | `/users/me/address`  | PUT    | 👤     | Upsert shipping address (creates if none exists)    |

---

### 3. Admin — User Management API Set

> Admin-only control over all platform user accounts.

| #   | Endpoint                          | Method | Access | Notes                                                                 |
| --- | --------------------------------- | ------ | ------ | --------------------------------------------------------------------- |
| 3.1 | `/users`                          | GET    | 🔑     | Paginated user list; filterable by role, status, search by name/email |
| 3.2 | `/users/{user_id}`                | GET    | 🔑     | View any user profile                                                 |
| 3.3 | `/users/admin`                    | POST   | 🔑     | Register a new admin-role account                                     |
| 3.4 | `/users/{user_id}/suspend`        | PATCH  | 🔑     | Set status → SUSPENDED                                                |
| 3.5 | `/users/{user_id}/activate`       | PATCH  | 🔑     | Set status → ACTIVE (unsuspend)                                       |
| 3.6 | `/users/{user_id}/password-reset` | POST   | 🔑     | Force-set a new password for a user (admin action)                    |
| 3.7 | `/users/{user_id}`                | DELETE | 🔑     | Soft-delete a user account                                            |

---

### 4. Book Catalog API Set

> Public browsing for customers; full CRUD and asset management for admins.
> Both access levels share resource paths; RBAC enforced per method.

| #   | Endpoint                      | Method | Access | Notes                                                                                                                                                                                                                           |
| --- | ----------------------------- | ------ | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 4.1 | `/books`                      | GET    | 🌐     | Paginated list; filters: `collection_id`, `category_id`, `author_id`, `publisher_id`, language, price range, in-stock; full-text search by title, author name. `collection_id` resolves via `book → category → collection` join |
| 4.2 | `/books/{book_id}`            | GET    | 🌐     | Full book detail (authors, publisher, category, stock)                                                                                                                                                                          |
| 4.3 | `/books`                      | POST   | 🔑     | Create book record                                                                                                                                                                                                              |
| 4.4 | `/books/{book_id}`            | PATCH  | 🔑     | Update book metadata                                                                                                                                                                                                            |
| 4.5 | `/books/{book_id}`            | DELETE | 🔑     | Soft-delete book (permanent removal from all views)                                                                                                                                                                             |
| 4.6 | `/books/{book_id}/deactivate` | PATCH  | 🔑     | Hide from storefront without deleting (`deactivated_at`)                                                                                                                                                                        |
| 4.7 | `/books/{book_id}/activate`   | PATCH  | 🔑     | Restore deactivated book to storefront                                                                                                                                                                                          |
| 4.8 | `/books/{book_id}/stock`      | PATCH  | 🔑     | Set or adjust `stock_quantity`                                                                                                                                                                                                  |
| 4.9 | `/books/{book_id}/cover`      | POST   | 🔑     | Upload cover image (multipart); updates `cover_url` via storage service                                                                                                                                                         |

---

### 5. Category API Set

> Genre/category management. A category belongs to exactly one Collection
> (`collection_id` FK). Public read; admin write. Deleting a category sets
> `book.category_id → NULL` on associated books (ON DELETE SET NULL).

| #   | Endpoint                    | Method | Access | Notes                                                                                          |
| --- | --------------------------- | ------ | ------ | ---------------------------------------------------------------------------------------------- |
| 5.1 | `/categories`               | GET    | 🌐     | List all categories; optional filter `?collection_id=` to get genres for a specific collection |
| 5.2 | `/categories/{category_id}` | GET    | 🌐     | Category detail                                                                                |
| 5.3 | `/categories`               | POST   | 🔑     | Create category; body must include `collection_id`                                             |
| 5.4 | `/categories/{category_id}` | PATCH  | 🔑     | Update name, url_slug, or reassign to a different collection                                   |
| 5.5 | `/categories/{category_id}` | DELETE | 🔑     | Soft-delete category; associated books lose their category assignment                          |

---

### 6. Author API Set

> Author management. Public read; admin write. Authors are created independently
> and assigned to books via the Book payload.

| #   | Endpoint               | Method | Access | Notes                 |
| --- | ---------------------- | ------ | ------ | --------------------- |
| 6.1 | `/authors`             | GET    | 🌐     | Paginated author list |
| 6.2 | `/authors/{author_id}` | GET    | 🌐     | Author detail         |
| 6.3 | `/authors`             | POST   | 🔑     | Create author         |
| 6.4 | `/authors/{author_id}` | PATCH  | 🔑     | Update author         |
| 6.5 | `/authors/{author_id}` | DELETE | 🔑     | Soft-delete author    |

---

### 7. Publisher API Set

> Publisher management. Public read; admin write.

| #   | Endpoint                     | Method | Access | Notes                    |
| --- | ---------------------------- | ------ | ------ | ------------------------ |
| 7.1 | `/publishers`                | GET    | 🌐     | Paginated publisher list |
| 7.2 | `/publishers/{publisher_id}` | GET    | 🌐     | Publisher detail         |
| 7.3 | `/publishers`                | POST   | 🔑     | Create publisher         |
| 7.4 | `/publishers/{publisher_id}` | PATCH  | 🔑     | Update publisher         |
| 7.5 | `/publishers/{publisher_id}` | DELETE | 🔑     | Soft-delete publisher    |

---

### 8. Collection API Set

> Top-level catalogue groupings (e.g. "Fiction", "Science & Technology").
> A Collection contains Categories; Categories contain Books. There is no
> direct Collection↔Book link — a book belongs to a collection implicitly
> through its `category.collection_id`. Therefore there are no
> "add/remove book from collection" endpoints; book-to-collection association
> is managed by assigning the book a `category_id` (via the Book endpoints).
> The `CollectionEntity` eagerly loads its categories (`lazy="selectin"`),
> so the detail endpoint returns the collection with its category list.

| #   | Endpoint                       | Method | Access | Notes                                                                        |
| --- | ------------------------------ | ------ | ------ | ---------------------------------------------------------------------------- |
| 8.1 | `/collections`                 | GET    | 🌐     | List all collections; each item includes its embedded category list          |
| 8.2 | `/collections/{collection_id}` | GET    | 🌐     | Collection detail with full category list embedded                           |
| 8.3 | `/collections`                 | POST   | 🔑     | Create collection                                                            |
| 8.4 | `/collections/{collection_id}` | PATCH  | 🔑     | Update name or url_slug                                                      |
| 8.5 | `/collections/{collection_id}` | DELETE | 🔑     | Soft-delete collection; cascades soft-delete to all its categories in the DB |

---

### 9. Cart API Set

> Manages the authenticated customer's active shopping cart (one per user).

| #   | Endpoint                | Method | Access | Notes                                               |
| --- | ----------------------- | ------ | ------ | --------------------------------------------------- |
| 9.1 | `/cart`                 | GET    | 👤     | Get own cart with all items                         |
| 9.2 | `/cart/items`           | POST   | 👤     | Add book to cart; duplicate book increases quantity |
| 9.3 | `/cart/items/{item_id}` | PATCH  | 👤     | Update item quantity                                |
| 9.4 | `/cart/items/{item_id}` | DELETE | 👤     | Remove item from cart                               |
| 9.5 | `/cart`                 | DELETE | 👤     | Clear all cart items                                |

---

### 10. Wishlist API Set

> Saved-for-later list per customer.

| #    | Endpoint                                 | Method | Access | Notes                           |
| ---- | ---------------------------------------- | ------ | ------ | ------------------------------- |
| 10.1 | `/wishlist`                              | GET    | 👤     | Get own wishlist with all items |
| 10.2 | `/wishlist/items`                        | POST   | 👤     | Add book to wishlist            |
| 10.3 | `/wishlist/items/{item_id}`              | DELETE | 👤     | Remove book from wishlist       |
| 10.4 | `/wishlist/items/{item_id}/move-to-cart` | POST   | 👤     | Move item from wishlist to cart |

---

### 11. Order API Set

> Checkout and order lifecycle. Customers manage their own orders; admins manage
> fulfillment across all orders.

| #    | Endpoint                     | Method | Access | Notes                                                                                                  |
| ---- | ---------------------------- | ------ | ------ | ------------------------------------------------------------------------------------------------------ |
| 11.1 | `/orders`                    | POST   | 👤     | Place order from cart; snapshots item prices; clears cart on success                                   |
| 11.2 | `/orders/{order_id}/payment` | POST   | 👤     | Simulated payment: body `{ outcome: "success" \| "failure" }`; transitions PENDING → PAID or CANCELLED |
| 11.3 | `/orders`                    | GET    | 👤🔑   | Customer: own orders. Admin: all orders, filterable by status, user, date range                        |
| 11.4 | `/orders/{order_id}`         | GET    | 👤🔑   | Customer: own order only. Admin: any order                                                             |
| 11.5 | `/orders/{order_id}/cancel`  | POST   | 👤🔑   | Cancel order (customer: own PENDING; admin: any)                                                       |
| 11.6 | `/orders/{order_id}/status`  | PATCH  | 🔑     | Update fulfillment status: PAID → SHIPPED → DELIVERED                                                  |

---

### 12. Review API Set

> Customer reviews and ratings; admin moderation.

| #    | Endpoint                          | Method | Access | Notes                                                                                                   |
| ---- | --------------------------------- | ------ | ------ | ------------------------------------------------------------------------------------------------------- |
| 12.1 | `/books/{book_id}/reviews`        | GET    | 🌐     | Paginated reviews for a book (only visible/non-hidden)                                                  |
| 12.2 | `/books/{book_id}/reviews`        | POST   | 👤     | Submit review; only allowed if user has a DELIVERED order containing this book                          |
| 12.3 | `/users/me/reviews`               | GET    | 👤     | List own reviews                                                                                        |
| 12.4 | `/users/me/reviews/{review_id}`   | PATCH  | 👤     | Update own review (rating, text)                                                                        |
| 12.5 | `/users/me/reviews/{review_id}`   | DELETE | 👤     | Delete own review                                                                                       |
| 12.6 | `/reviews`                        | GET    | 🔑     | Paginated list of all reviews; filters: `book_id`, `user_id`, `is_hidden`; includes hidden/soft-deleted |
| 12.7 | `/reviews/{review_id}/visibility` | PATCH  | 🔑     | Hide or restore a review (moderation)                                                                   |
| 12.8 | `/reviews/{review_id}`            | DELETE | 🔑     | Admin hard-remove a review                                                                              |

---

### 13. Notification API Set

> In-app notification inbox for authenticated users.

| #    | Endpoint                                | Method | Access | Notes                                                   |
| ---- | --------------------------------------- | ------ | ------ | ------------------------------------------------------- |
| 13.1 | `/notifications`                        | GET    | 👤🔑   | Paginated notification list; filterable by read/unread  |
| 13.2 | `/notifications/unread-count`           | GET    | 👤🔑   | Returns unread notification count (for badge/indicator) |
| 13.3 | `/notifications/{notification_id}/read` | PATCH  | 👤🔑   | Mark single notification as read                        |
| 13.4 | `/notifications/read-all`               | PATCH  | 👤🔑   | Mark all notifications as read                          |
| 13.5 | `/notifications/{notification_id}`      | DELETE | 👤🔑   | Delete a notification                                   |

---

### 14. Admin — Inventory Dashboard API Set

> Aggregated stock metrics for the admin inventory view. Synchronous (small
> aggregation queries, not report-scale).

| #    | Endpoint                  | Method | Access | Notes                                                                                |
| ---- | ------------------------- | ------ | ------ | ------------------------------------------------------------------------------------ |
| 14.1 | `/inventory/metrics`      | GET    | 🔑     | Returns: total SKU count, out-of-stock count, low-stock count, total inventory value |
| 14.2 | `/inventory/low-stock`    | GET    | 🔑     | Paginated list of books below a stock threshold (default or query param)             |
| 14.3 | `/inventory/out-of-stock` | GET    | 🔑     | Paginated list of out-of-stock books                                                 |

---

### 15. Admin — Reports & Analytics API Set

> Async report generation via Celery. Sales reports scan large datasets and
> render to PDF/CSV — synchronous delivery would risk HTTP timeouts and block
> server threads. The existing Celery worker (already handling email tasks)
> handles report jobs at no extra infrastructure cost. Clients poll for
> completion, then download the file from a signed MinIO/S3 URL.

| #    | Endpoint                          | Method | Access | Notes                                                                                                                                                                                  |
| ---- | --------------------------------- | ------ | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 15.1 | `/reports/jobs`                   | POST   | 🔑     | Submit report job: `{ type, date_from, date_to, format: "pdf"\|"csv" }`. Types: `sales_summary`, `top_books`, `top_authors`, `monthly_volume`. Returns `{ job_id, status: "pending" }` |
| 15.2 | `/reports/jobs/{job_id}`          | GET    | 🔑     | Poll job status: `{ job_id, status, created_at, completed_at?, download_url? }`                                                                                                        |
| 15.3 | `/reports/jobs/{job_id}/download` | GET    | 🔑     | Stream the generated file; 404 if not yet complete                                                                                                                                     |
| 15.4 | `/reports/jobs`                   | GET    | 🔑     | Paginated history of submitted report jobs                                                                                                                                             |

---

## Summary

| API Set                         | Endpoint Count | Primary Domain                     |
| ------------------------------- | -------------- | ---------------------------------- |
| 1. Auth                         | 10             | Authentication & account lifecycle |
| 2. User Profile                 | 8              | Self-service account management    |
| 3. Admin – User Management      | 7              | User account administration        |
| 4. Book Catalog                 | 9              | Product browsing & admin CRUD      |
| 5. Category                     | 5              | Genre management                   |
| 6. Author                       | 5              | Author management                  |
| 7. Publisher                    | 5              | Publisher management               |
| 8. Collection                   | 5              | Top-level catalogue grouping       |
| 9. Cart                         | 5              | Shopping cart                      |
| 10. Wishlist                    | 4              | Saved-for-later                    |
| 11. Order                       | 6              | Checkout & fulfillment             |
| 12. Review                      | 8              | Ratings & moderation               |
| 13. Notification                | 5              | In-app inbox                       |
| 14. Admin – Inventory Dashboard | 2              | Stock metrics                      |
| 15. Admin – Reports & Analytics | 4              | Async report jobs                  |
| **Total**                       | **88**         |                                    |
