# Bukoo Web App — Frontend URL Catalog

## Context

This catalog defines the complete set of frontend routes for the Bukoo web
application. It is the frontend counterpart to `api-endpoint-catalog.md` and
serves as the implementation roadmap for all React pages. Each row is one
route component to build. Existing routes are marked **existing**.

Routes are registered in `frontend/src/App.jsx`. The admin area lives within
the same React app under `/admin/*`; access is enforced per-route by checking
the authenticated user's role.

## Design Decisions

| Decision                    | Choice                                                                        | Rationale                                                                              |
| --------------------------- | ----------------------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| Admin portal integration    | `/admin/*` within the same React app; role-redirected after login             | Single codebase; role guard per route; consistent with RBAC-only separation on backend |
| Checkout flow               | Multi-step: `/checkout` → `/checkout/payment` → `/checkout/confirmation`      | Each step maps to a distinct API call; prevents accidental double-submission           |
| OAuth callback path         | `/oauth/callback` (existing page `OAuthCallback.jsx`)                         | Matches the redirect target already wired in `App.jsx`; UI can be updated later        |
| Profile path for both roles | `/account/profile` and `/account/password` accessible to 👤 and 🔑            | Avoids duplicating profile pages under `/admin`; admins manage their own account here  |
| Review moderation entry     | `/admin/reviews` with book-search first; detail per-book                      | No "list all reviews" API exists; moderation actions target individual review IDs      |
| URL parameters              | Slug-based where available (`:collectionSlug`, `:handle`); ID-based elsewhere | Slug is already part of the domain model for books and collections                     |

## Access Level Legend

| Symbol | Meaning                               |
| ------ | ------------------------------------- |
| 🌐     | Public — no authentication required   |
| 👤     | Customer — authenticated, `USER` role |
| 🔑     | Admin — authenticated, `ADMIN` role   |
| 👤🔑   | Both authenticated roles              |

---

## URL Catalog

---

### 1. Auth & OAuth

| #   | Path               | Access | Involved APIs | Notes                                                                                                                     |
| --- | ------------------ | ------ | ------------- | ------------------------------------------------------------------------------------------------------------------------- |
| 1.1 | `/register`        | 🌐     | 1.1           | Account registration form. **Existing.** Reimplementation needed to align with new API.                                   |
| 1.2 | `/verify-email`    | 🌐     | 1.2, 1.3      | Email OTP entry field; resend link triggers 1.3                                                                           |
| 1.3 | `/login`           | 🌐     | 1.4, 1.5a     | Credential login form + "Sign in with Google" button. **Existing.** Reimplementation needed.                              |
| 1.4 | `/oauth/callback`  | 🌐     | 1.5b          | OAuth callback landing; reads `?error=` param and shows error or redirects on success. **Existing** (`OAuthCallback.jsx`) |
| 1.5 | `/forgot-password` | 🌐     | 1.7           | Email submission form to trigger password reset OTP                                                                       |
| 1.6 | `/reset-password`  | 🌐     | 1.8, 1.9      | Validates reset token on load (1.8); renders new-password form on valid; submits via 1.9                                  |

---

### 2. Storefront — Public Browsing

| #   | Path                | Access | Involved APIs | Notes                                                                                                                                 |
| --- | ------------------- | ------ | ------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| 2.1 | `/`                 | 🌐     | 8.1, 4.1      | Home / landing page; featured collections and highlighted books. **Existing.**                                                        |
| 2.2 | `/shop`             | 🌐     | 4.1, 8.1      | Full book catalog; paginated grid with filter sidebar (collection, category, author, publisher, price range, in-stock). **Existing.** |
| 2.3 | `/shop/:collection` | 🌐     | 4.1, 8.2, 5.1 | Catalog pre-filtered by collection; collection name + category sub-navigation. **Existing.**                                          |
| 2.4 | `/search`           | 🌐     | 4.1           | Full-text search results driven by `?q=` query param; reuses catalog filters. **Existing.**                                           |
| 2.5 | `/product/:handle`  | 🌐     | 4.2, 12.1     | Book detail: cover, metadata, stock status, paginated reviews list. **Existing.**                                                     |

---

### 3. Customer — Account & Profile

> All routes in this section require `USER` role unless noted. Redirect to `/login` if unauthenticated.

| #   | Path                       | Access | Involved APIs                | Notes                                                                             |
| --- | -------------------------- | ------ | ---------------------------- | --------------------------------------------------------------------------------- |
| 3.1 | `/account`                 | 👤     | 2.1                          | Account overview hub; shows profile summary, links to all sub-sections            |
| 3.2 | `/account/profile`         | 👤🔑   | 2.1, 2.2, 2.4, 2.5           | View and edit profile (name, date of birth); avatar upload (2.4) and remove (2.5) |
| 3.3 | `/account/password`        | 👤🔑   | 2.6                          | Change password form; requires current password                                   |
| 3.4 | `/account/address`         | 👤     | 2.7, 2.8                     | View and upsert shipping address                                                  |
| 3.5 | `/account/orders`          | 👤     | 11.3                         | Customer order history list; filterable by status                                 |
| 3.6 | `/account/orders/:orderId` | 👤     | 11.4, 11.5                   | Order detail: items, prices, status; cancel action for PENDING orders (11.5)      |
| 3.7 | `/account/reviews`         | 👤     | 12.3, 12.4, 12.5             | Own submitted reviews list; inline edit (12.4) and delete (12.5) actions          |
| 3.8 | `/account/notifications`   | 👤     | 13.1, 13.2, 13.3, 13.4, 13.5 | Customer notification inbox; unread badge (13.2), mark-read, delete               |
| 3.9 | `/account/delete`          | 👤     | 2.3                          | Account deletion confirmation; warns user of permanent data removal               |

---

### 4. Customer — Shopping Flow

> All routes in this section require `USER` role. Cart and wishlist redirect to `/login` if unauthenticated.

| #   | Path                     | Access | Involved APIs           | Notes                                                                                   |
| --- | ------------------------ | ------ | ----------------------- | --------------------------------------------------------------------------------------- |
| 4.1 | `/cart`                  | 👤     | 9.1, 9.2, 9.3, 9.4, 9.5 | Shopping cart: item list, quantity update (9.3), remove (9.4), clear all (9.5)          |
| 4.2 | `/wishlist`              | 👤     | 10.1, 10.2, 10.3, 10.4  | Saved-for-later list; remove (10.3) and move-to-cart (10.4) actions                     |
| 4.3 | `/checkout`              | 👤     | 2.7, 11.1               | **Step 1** — Review cart items + confirm delivery address; place order on submit (11.1) |
| 4.4 | `/checkout/payment`      | 👤     | 11.2                    | **Step 2** — Simulated payment: choose success or failure outcome and submit            |
| 4.5 | `/checkout/confirmation` | 👤     | 11.4                    | **Step 3** — Order confirmed: order summary and link to `/account/orders/:orderId`      |

---

### 5. Admin — Dashboard

> All admin routes require `ADMIN` role. Redirect to `/login` if unauthenticated; redirect to `/` if authenticated as `USER`.

| #   | Path                   | Access | Involved APIs                | Notes                                                                                                |
| --- | ---------------------- | ------ | ---------------------------- | ---------------------------------------------------------------------------------------------------- |
| 5.1 | `/admin`               | 🔑     | 14.1, 11.3, 3.1              | Admin home: inventory metrics (14.1), recent orders snapshot (11.3), recent user registrations (3.1) |
| 5.2 | `/admin/notifications` | 🔑     | 13.1, 13.2, 13.3, 13.4, 13.5 | Admin notification inbox; unread badge (13.2), mark-read, delete                                     |

---

### 6. Admin — Catalog Management

| #    | Path                               | Access | Involved APIs                     | Notes                                                                                                             |
| ---- | ---------------------------------- | ------ | --------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 6.1  | `/admin/books`                     | 🔑     | 4.1                               | Book list with search, filters; deactivate/activate toggles inline                                                |
| 6.2  | `/admin/books/new`                 | 🔑     | 4.3, 5.1, 6.1, 7.1                | Create book form; selects category (5.1), authors (6.1), publisher (7.1)                                          |
| 6.3  | `/admin/books/:bookId`             | 🔑     | 4.2, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9 | Book detail/edit: metadata (4.4), cover upload (4.9), stock adjust (4.8), deactivate (4.6/4.7), soft-delete (4.5) |
| 6.4  | `/admin/collections`               | 🔑     | 8.1, 8.3, 8.4, 8.5                | Collection list; create (8.3), edit (8.4), soft-delete (8.5)                                                      |
| 6.5  | `/admin/collections/:collectionId` | 🔑     | 8.2, 8.4, 8.5                     | Collection detail: edit name/slug (8.4), soft-delete (8.5); shows embedded category list                          |
| 6.6  | `/admin/categories`                | 🔑     | 5.1, 5.3, 5.4, 5.5                | Category list; create (5.3), edit (5.4), soft-delete (5.5)                                                        |
| 6.7  | `/admin/categories/:categoryId`    | 🔑     | 5.2, 5.4, 5.5                     | Category detail/edit: name, slug, reassign collection (5.4), soft-delete (5.5)                                    |
| 6.8  | `/admin/authors`                   | 🔑     | 6.1, 6.3, 6.4, 6.5                | Author list; create (6.3), edit (6.4), soft-delete (6.5)                                                          |
| 6.9  | `/admin/authors/:authorId`         | 🔑     | 6.2, 6.4, 6.5                     | Author detail/edit (6.4), soft-delete (6.5)                                                                       |
| 6.10 | `/admin/publishers`                | 🔑     | 7.1, 7.3, 7.4, 7.5                | Publisher list; create (7.3), edit (7.4), soft-delete (7.5)                                                       |
| 6.11 | `/admin/publishers/:publisherId`   | 🔑     | 7.2, 7.4, 7.5                     | Publisher detail/edit (7.4), soft-delete (7.5)                                                                    |

---

### 7. Admin — User Management

| #   | Path                   | Access | Involved APIs           | Notes                                                                                           |
| --- | ---------------------- | ------ | ----------------------- | ----------------------------------------------------------------------------------------------- |
| 7.1 | `/admin/users`         | 🔑     | 3.1                     | User list; filter by role, status; search by name/email                                         |
| 7.2 | `/admin/users/new`     | 🔑     | 3.3                     | Register new admin-role account                                                                 |
| 7.3 | `/admin/users/:userId` | 🔑     | 3.2, 3.4, 3.5, 3.6, 3.7 | User profile view; suspend (3.4), activate (3.5), force password reset (3.6), soft-delete (3.7) |

---

### 8. Admin — Order Management

| #   | Path                     | Access | Involved APIs    | Notes                                                                                     |
| --- | ------------------------ | ------ | ---------------- | ----------------------------------------------------------------------------------------- |
| 8.1 | `/admin/orders`          | 🔑     | 11.3             | All orders list; filter by status, user, date range                                       |
| 8.2 | `/admin/orders/:orderId` | 🔑     | 11.4, 11.5, 11.6 | Order detail: items, customer info, cancel, status progression PAID → SHIPPED → DELIVERED |

---

### 9. Admin — Review Moderation

| #   | Path             | Access | Involved APIs    | Notes                                                                                                                                       |
| --- | ---------------- | ------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| 9.1 | `/admin/reviews` | 🔑     | 12.1, 12.6, 12.7 | Search for a book to load its reviews (12.1); hide/restore (12.6) or hard-delete (12.7) individual reviews. No list-all-reviews API exists. |

---

### 10. Admin — Inventory & Reports

| #    | Path               | Access | Involved APIs          | Notes                                                                                                                              |
| ---- | ------------------ | ------ | ---------------------- | ---------------------------------------------------------------------------------------------------------------------------------- |
| 10.1 | `/admin/inventory` | 🔑     | 14.1, 14.2             | Inventory dashboard: total SKUs, out-of-stock count, low-stock count, inventory value (14.1); paginated low-stock book list (14.2) |
| 10.2 | `/admin/reports`   | 🔑     | 15.1, 15.2, 15.3, 15.4 | Reports hub: submit new job (15.1), job history list (15.4), poll status (15.2), download completed report (15.3)                  |

---

## Summary

| Section                         | Route Count | Primary Domain                                      |
| ------------------------------- | ----------- | --------------------------------------------------- |
| 1. Auth & OAuth                 | 6           | Authentication, registration, password flow         |
| 2. Storefront — Public          | 5           | Book browsing and search                            |
| 3. Customer — Account           | 9           | Profile, orders, reviews, notifications             |
| 4. Customer — Shopping          | 5           | Cart, wishlist, checkout flow                       |
| 5. Admin — Dashboard            | 2           | Overview metrics and notifications                  |
| 6. Admin — Catalog Management   | 11          | Books, collections, categories, authors, publishers |
| 7. Admin — User Management      | 3           | User list, create admin, user detail                |
| 8. Admin — Order Management     | 2           | Order list and fulfillment                          |
| 9. Admin — Review Moderation    | 1           | Review hide/delete                                  |
| 10. Admin — Inventory & Reports | 2           | Stock metrics and async report jobs                 |
| **Total**                       | **46**      |                                                     |
