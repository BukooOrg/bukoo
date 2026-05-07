# Web App Router Implementation Plan

## Objective

Scaffold the complete React routing structure for the Bukoo web app based on
`.claude/context/web-app-url-catalog.md`. This covers layout components, route
guards, page file organisation, and a full App.jsx router rewrite.

## Scope

| In scope                                       | Out of scope                              |
| ---------------------------------------------- | ----------------------------------------- |
| Layout components (Storefront, Auth, Admin)    | Implementing real page UI beyond skeleton |
| Route guard components                         | Backend API changes                       |
| Migrating `AuthContext` from `apiFetch` to SDK | SDK regeneration (`make generate-sdk`)    |
| Renaming `pages/` → `pages_legacy/`            | Modifying any file inside `pages_legacy/` |
| Creating new `pages/` with nested structure    | CSS / design work                         |
| Rewriting `App.jsx` router                     | Any file outside `frontend/src/`          |

## Architectural Constraints

- All API calls must go through instances exported from `frontend/src/lib/apiClient.js`
  using the `@bukoo/api-client` generated SDK. Raw `fetch()` and `apiFetch` must
  not be used in new code.
- Layout routes use React Router v7 `<Outlet>` — child routes render inside the
  parent layout without prop-drilling.
- Guard components use `<Outlet>` on success and `<Navigate>` on failure; they
  never render page UI themselves.
- Page files use **default exports**. Shared components use **named exports**.
- File naming: lowercase kebab-case for component files; PascalCase for the
  exported function name inside.

---

## Phase 1 — Layout Components

Create three layout components in `frontend/src/components/layout/`.

### 1.1 `storefront-layout.jsx`

Replaces the shell `<div>` currently wrapping all routes in App.jsx.

```
<div class="flex flex-col min-h-screen">
  <Header />
  <main class="flex-1">
    <Outlet />          ← child routes render here
  </main>
  <Footer />
  <Toaster />
</div>
```

### 1.2 `auth-layout.jsx`

No Header or Footer. Auth pages manage their own full-screen layout internally.

```
<>
  <Outlet />
  <Toaster />
</>
```

### 1.3 `admin-layout.jsx`

Skeleton admin shell. Sidebar and top bar are placeholders — UI to be designed
later. Uses `<Outlet>` for page content.

```
<div class="flex min-h-screen">
  <aside>  ← sidebar placeholder
    <nav>Admin Nav</nav>
  </aside>
  <div class="flex flex-col flex-1">
    <header>Admin Header</header>    ← top bar placeholder
    <main class="flex-1 p-6">
      <Outlet />
    </main>
  </div>
  <Toaster />
</div>
```

---

## Phase 2a — Migrate AuthContext to SDK

**File:** `frontend/src/context/AuthContext.jsx`

**Problem:** `AuthContext` currently calls `apiFetch('/api/auth/me')` (raw fetch,
legacy pattern). This violates the architectural constraint that all API calls
go through `apiClient.js`.

**Change:** Replace `apiFetch` with `usersApi.getMe()` from
`frontend/src/lib/apiClient.js`.

```js
// Before
import { apiFetch } from "../lib/api";
const userData = await apiFetch("/api/auth/me");

// After
import { usersApi } from "../lib/apiClient";
const response = await usersApi.getMe();
```

The `user` object stored in context will be the SDK response object. The role
field is accessed as `user?.data?.role` (SDK returns the full envelope with a
`data` wrapper). Role values are lowercase: `'admin'` and `'user'`.

> **Note:** The SDK method is confirmed as `getMe()` on `UsersApi`.

---

## Phase 2b — Route Guard Components

Create three guard components in `frontend/src/components/guards/`.

All guards:

- Return a loading spinner while `loading === true` (avoids flash-redirect on
  initial page load).
- Use `<Navigate replace>` for redirects (replaces history entry so the browser
  back button does not loop).
- Render `<Outlet />` on success (child routes render inside).

### `protected-route.jsx` — 👤🔑 Any authenticated user

| State                    | Behaviour                  |
| ------------------------ | -------------------------- |
| Loading                  | Show spinner               |
| Authenticated (any role) | `<Outlet />`               |
| Unauthenticated          | `<Navigate to="/login" />` |

### `customer-route.jsx` — 👤 USER role only

| State                           | Behaviour                  |
| ------------------------------- | -------------------------- |
| Loading                         | Show spinner               |
| Authenticated, role = `'user'`  | `<Outlet />`               |
| Authenticated, role = `'admin'` | `<Navigate to="/admin" />` |
| Unauthenticated                 | `<Navigate to="/login" />` |

### `admin-route.jsx` — 🔑 ADMIN role only

| State                           | Behaviour                  |
| ------------------------------- | -------------------------- |
| Loading                         | Show spinner               |
| Authenticated, role = `'admin'` | `<Outlet />`               |
| Authenticated, role = `'user'`  | `<Navigate to="/" />`      |
| Unauthenticated                 | `<Navigate to="/login" />` |

Role is read from `user?.data?.role`. The `UserRole` enum values from the backend are
`'user'` and `'admin'` (StrEnum, serialised as lowercase plain strings).

---

## Phase 3 — Rename pages/ → pages_legacy/

```bash
mv frontend/src/pages frontend/src/pages_legacy
```

All existing files plus any sub-directories move here **untouched**.
No file inside `pages_legacy/` is modified at any point.

---

## Phase 4 — New pages/ Directory Structure

**Rule:** If the file exists in `pages_legacy/`, copy its content verbatim to
the new path. Otherwise create a named skeleton:

```jsx
export default function PageName() {
  return <div>PageName</div>;
}
```

### Full file tree

```
frontend/src/pages/
│
├── auth/
│   ├── LoginPage.jsx                   ← copied / new
│   ├── RegisterPage.jsx                ← copied / new
│   ├── OAuthCallbackPage.jsx           ← copied / new
│   ├── VerifyEmailPage.jsx             ← skeleton  (route 1.2)
│   ├── ForgotPasswordPage.jsx          ← skeleton  (route 1.5)
│   └── ResetPasswordPage.jsx           ← skeleton  (route 1.6)
│
├── storefront/
│   ├── HomePage.jsx                    ← copied / new
│   ├── ShopPage.jsx                    ← copied / new
│   ├── ProductDetailPage.jsx           ← copied / new
│   └── NotFoundPage.jsx                ← extracted from inline 404 in App.jsx
│
├── account/
│   ├── AccountPage.jsx                 ← skeleton  (route 3.1)
│   ├── ProfilePage.jsx                 ← skeleton  (route 3.2)
│   ├── PasswordPage.jsx                ← skeleton  (route 3.3)
│   ├── AddressPage.jsx                 ← skeleton  (route 3.4)
│   ├── OrdersPage.jsx                  ← skeleton  (route 3.5)
│   ├── OrderDetailPage.jsx             ← skeleton  (route 3.6)
│   ├── ReviewsPage.jsx                 ← skeleton  (route 3.7)
│   ├── NotificationsPage.jsx           ← skeleton  (route 3.8)
│   └── DeleteAccountPage.jsx           ← skeleton  (route 3.9)
│
├── shopping/
│   ├── CartPage.jsx                    ← skeleton  (route 4.1)
│   ├── WishlistPage.jsx                ← skeleton  (route 4.2)
│   ├── CheckoutPage.jsx                ← skeleton  (route 4.3)
│   ├── CheckoutPaymentPage.jsx         ← skeleton  (route 4.4)
│   └── CheckoutConfirmationPage.jsx    ← skeleton  (route 4.5)
│
└── admin/
    ├── DashboardPage.jsx               ← skeleton  (route 5.1)
    ├── NotificationsPage.jsx           ← skeleton  (route 5.2)
    ├── catalog/
    │   ├── BooksPage.jsx               ← skeleton  (route 6.1)
    │   ├── BookNewPage.jsx             ← skeleton  (route 6.2)
    │   ├── BookDetailPage.jsx          ← skeleton  (route 6.3)
    │   ├── CollectionsPage.jsx         ← skeleton  (route 6.4)
    │   ├── CollectionDetailPage.jsx    ← skeleton  (route 6.5)
    │   ├── CategoriesPage.jsx          ← skeleton  (route 6.6)
    │   ├── CategoryDetailPage.jsx      ← skeleton  (route 6.7)
    │   ├── AuthorsPage.jsx             ← skeleton  (route 6.8)
    │   ├── AuthorDetailPage.jsx        ← skeleton  (route 6.9)
    │   ├── PublishersPage.jsx          ← skeleton  (route 6.10)
    │   └── PublisherDetailPage.jsx     ← skeleton  (route 6.11)
    ├── users/
    │   ├── UsersPage.jsx               ← skeleton  (route 7.1)
    │   ├── UserNewPage.jsx             ← skeleton  (route 7.2)
    │   └── UserDetailPage.jsx          ← skeleton  (route 7.3)
    ├── orders/
    │   ├── OrdersPage.jsx              ← skeleton  (route 8.1)
    │   └── OrderDetailPage.jsx         ← skeleton  (route 8.2)
    ├── reviews/
    │   └── ReviewsPage.jsx             ← skeleton  (route 9.1)
    └── inventory/
        ├── InventoryPage.jsx           ← skeleton  (route 10.1)
        └── ReportsPage.jsx             ← skeleton  (route 10.2)
```

---

## Phase 5 — Rewrite App.jsx

Comment out the existing `<Router>` block (keep it in the file for reference).
Define the new router below it.

### Route tree

```
<AuthProvider>
  <CartProvider>
    <BrowserRouter>
      <Routes>

        {/* ── AUTH LAYOUT — no Header/Footer ───────────────────────── */}
        <Route element={<AuthLayout />}>
          <Route path="/login"            element={<LoginPage />} />
          <Route path="/register"         element={<RegisterPage />} />
          <Route path="/oauth/callback"   element={<OAuthCallbackPage />} />
          <Route path="/verify-email"     element={<VerifyEmailPage />} />
          <Route path="/forgot-password"  element={<ForgotPasswordPage />} />
          <Route path="/reset-password"   element={<ResetPasswordPage />} />
        </Route>

        {/* ── STOREFRONT LAYOUT — Header + Footer ──────────────────── */}
        <Route element={<StorefrontLayout />}>

          {/* 🌐 Public */}
          <Route path="/"                     element={<HomePage />} />
          <Route path="/shop"                 element={<ShopPage />} />
          <Route path="/shop/:collection"     element={<ShopPage />} />
          <Route path="/search"               element={<ShopPage />} />
          <Route path="/product/:handle"      element={<ProductDetailPage />} />

          {/* 👤🔑 Any authenticated user */}
          <Route element={<ProtectedRoute />}>
            <Route path="/account/profile"  element={<ProfilePage />} />
            <Route path="/account/password" element={<PasswordPage />} />
          </Route>

          {/* 👤 Customer only */}
          <Route element={<CustomerRoute />}>
            <Route path="/account"                    element={<AccountPage />} />
            <Route path="/account/address"            element={<AddressPage />} />
            <Route path="/account/orders"             element={<AccountOrdersPage />} />
            <Route path="/account/orders/:orderId"    element={<AccountOrderDetailPage />} />
            <Route path="/account/reviews"            element={<AccountReviewsPage />} />
            <Route path="/account/notifications"      element={<AccountNotificationsPage />} />
            <Route path="/account/delete"             element={<DeleteAccountPage />} />
            <Route path="/cart"                       element={<CartPage />} />
            <Route path="/wishlist"                   element={<WishlistPage />} />
            <Route path="/checkout"                   element={<CheckoutPage />} />
            <Route path="/checkout/payment"           element={<CheckoutPaymentPage />} />
            <Route path="/checkout/confirmation"      element={<CheckoutConfirmationPage />} />
          </Route>

        </Route>{/* end StorefrontLayout */}

        {/* ── ADMIN LAYOUT — sidebar shell ─────────────────────────── */}
        <Route element={<AdminRoute />}>
          <Route element={<AdminLayout />}>

            {/* 🔑 Dashboard */}
            <Route path="/admin"               element={<AdminDashboardPage />} />
            <Route path="/admin/notifications" element={<AdminNotificationsPage />} />

            {/* 🔑 Catalog */}
            <Route path="/admin/books"                            element={<BooksPage />} />
            <Route path="/admin/books/new"                        element={<BookNewPage />} />
            <Route path="/admin/books/:bookId"                    element={<BookDetailPage />} />
            <Route path="/admin/collections"                      element={<CollectionsPage />} />
            <Route path="/admin/collections/:collectionId"        element={<CollectionDetailPage />} />
            <Route path="/admin/categories"                       element={<CategoriesPage />} />
            <Route path="/admin/categories/:categoryId"           element={<CategoryDetailPage />} />
            <Route path="/admin/authors"                          element={<AuthorsPage />} />
            <Route path="/admin/authors/:authorId"                element={<AuthorDetailPage />} />
            <Route path="/admin/publishers"                       element={<PublishersPage />} />
            <Route path="/admin/publishers/:publisherId"          element={<PublisherDetailPage />} />

            {/* 🔑 Users */}
            <Route path="/admin/users"           element={<UsersPage />} />
            <Route path="/admin/users/new"       element={<UserNewPage />} />
            <Route path="/admin/users/:userId"   element={<UserDetailPage />} />

            {/* 🔑 Orders */}
            <Route path="/admin/orders"            element={<AdminOrdersPage />} />
            <Route path="/admin/orders/:orderId"   element={<AdminOrderDetailPage />} />

            {/* 🔑 Reviews */}
            <Route path="/admin/reviews" element={<AdminReviewsPage />} />

            {/* 🔑 Inventory & Reports */}
            <Route path="/admin/inventory" element={<InventoryPage />} />
            <Route path="/admin/reports"   element={<ReportsPage />} />

          </Route>
        </Route>{/* end AdminRoute */}

        {/* ── 404 ──────────────────────────────────────────────────── */}
        <Route path="*" element={<NotFoundPage />} />

      </Routes>
    </BrowserRouter>
  </CartProvider>
</AuthProvider>
```

### Import organisation in App.jsx

Imports are grouped in this order, each group separated by a blank line:

1. React and React Router
2. Context providers
3. Guard components
4. Layout components
5. Auth pages
6. Storefront pages
7. Account pages
8. Shopping pages
9. Admin pages (Dashboard, Notifications, Catalog, Users, Orders, Reviews, Inventory)

---

## Execution Order

| Step | Action                                           | Depends on |
| ---- | ------------------------------------------------ | ---------- |
| 1    | Create `storefront-layout.jsx`                   | —          |
| 2    | Create `auth-layout.jsx`                         | —          |
| 3    | Create `admin-layout.jsx`                        | —          |
| 4    | Migrate `AuthContext` to `usersApi`              | —          |
| 5    | Create `protected-route.jsx`                     | Step 4     |
| 6    | Create `customer-route.jsx`                      | Step 4     |
| 7    | Create `admin-route.jsx`                         | Step 4     |
| 8    | Rename `pages/` → `pages_legacy/`                | —          |
| 9    | Create `pages/auth/` (6 files)                   | Step 8     |
| 10   | Create `pages/storefront/` (4 files)             | Step 8     |
| 11   | Create `pages/account/` (9 files)                | Step 8     |
| 12   | Create `pages/shopping/` (5 files)               | Step 8     |
| 13   | Create `pages/admin/` (21 files across sub-dirs) | Step 8     |
| 14   | Rewrite `App.jsx`                                | Steps 1–13 |

Steps 1–7 and steps 8–13 within their groups are independent and can be
parallelised.

---

## Files Modified / Created

| File                                                  | Action                                                |
| ----------------------------------------------------- | ----------------------------------------------------- |
| `frontend/src/context/AuthContext.jsx`                | Modified — swap `apiFetch` for `usersApi`             |
| `frontend/src/components/layout/StorefrontLayout.jsx` | Created                                               |
| `frontend/src/components/layout/AuthLayout.jsx`       | Created                                               |
| `frontend/src/components/layout/AdminLayout.jsx`      | Created                                               |
| `frontend/src/components/guards/ProtectedRoute.jsx`   | Created                                               |
| `frontend/src/components/guards/CustomerRoute.jsx`    | Created                                               |
| `frontend/src/components/guards/AdminRoute.jsx`       | Created                                               |
| `frontend/src/pages_legacy/`                          | Renamed from `pages/`                                 |
| `frontend/src/pages/**` (45 files)                    | Created                                               |
| `frontend/src/App.jsx`                                | Modified — old router commented out, new router added |
