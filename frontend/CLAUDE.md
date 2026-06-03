# frontend/CLAUDE.md

Detailed guide for the React/Vite frontend. Read `../CLAUDE.md` first for
monorepo commands, infrastructure services, and commit rules.

## Quick Reference

- **Dev server:** `:5173` via `make fe-dev`
- **Framework:** React 19, Vite 8, React Router DOM 7
- **Language:** JavaScript JSX — no TypeScript in frontend source
- **Path alias:** `@` resolves to `frontend/src/` (configured in `vite.config.js`)
- **API proxy:** Vite proxies `/api/*` → `http://localhost:8000` in dev (no CORS needed)
- **Package manager:** pnpm (workspace member of root `pnpm-workspace.yaml`)

## Directory Structure

```
frontend/src/
├── App.jsx             ← root component: provider stack + router + route table
├── main.jsx            ← React 19 createRoot entry point
├── actions/            ← thin API call wrappers (legacy raw fetch)
├── components/
│   ├── 3d-book/        ← Three.js / R3F 3D book visualization
│   ├── account/        ← account page sections
│   ├── admin/          ← admin page sections (shared across admin pages)
│   ├── auth/           ← auth form components
│   ├── cart/           ← CartContext, cart modal, add-to-cart button
│   ├── guards/         ← AdminRoute, CustomerRoute (role-based route guards)
│   ├── inventory/      ← inventory dashboard components
│   ├── layout/         ← header/, sidebar/, layout wrapper components
│   ├── notifications/  ← notification card, bell, inbox components
│   ├── orders/         ← order status badge, order item, order detail
│   ├── products/       ← product cards, variant selector
│   ├── reports/        ← report form, status badge, history table
│   ├── reviews/        ← review card, review form, rating display
│   ├── ui/             ← design system primitives
│   │   ├── forms/      ← button, input, field, select, checkbox
│   │   ├── feedback/   ← spinner, skeleton, alert, badge
│   │   ├── data-display/ ← table, list, card
│   │   ├── navigation/ ← tabs, breadcrumbs, pagination
│   │   ├── overlays/   ← dialog, sheet, tooltip, popover
│   │   └── misc/       ← separator, scroll-area, aspect-ratio
│   └── wishlist/       ← WishlistContext, wishlist item, move-to-cart button
├── context/            ← AuthContext (AuthProvider + useAuth hook)
├── hooks/              ← custom React hooks (useApiQuery, useApiMutation, etc.)
├── lib/                ← utilities, API client instances, constants
├── pages/
│   ├── account/        ← ProfilePage, PasswordPage, AddressPage, OrdersPage,
│   │                      OrderDetailPage, ReviewsPage, NotificationsPage,
│   │                      AccountPage, DeleteAccountPage
│   ├── admin/
│   │   ├── catalog/    ← BooksPage, BookDetailPage, BookNewPage,
│   │   │                  AuthorsPage, AuthorDetailPage, AuthorNewPage,
│   │   │                  PublishersPage, CategoriesPage, CollectionsPage, …
│   │   ├── inventory/  ← InventoryPage, ReportsPage
│   │   ├── orders/     ← OrdersPage, OrderDetailPage
│   │   ├── reviews/    ← ReviewsPage
│   │   ├── users/      ← UsersPage, UserDetailPage, UserNewPage
│   │   ├── DashboardPage.jsx
│   │   └── NotificationsPage.jsx
│   ├── auth/           ← LoginPage, RegisterPage, OAuthCallbackPage,
│   │                      VerifyEmailPage, ForgotPasswordPage,
│   │                      VerifyPasswordResetOtpPage, ResetPasswordPage
│   ├── shopping/       ← CartPage, WishlistPage, CheckoutPage,
│   │                      CheckoutPaymentPage, CheckoutConfirmationPage
│   └── storefront/     ← HomePage, ShopPage, ProductDetailPage, NotFoundPage
├── data/mock/          ← remaining mock JSON (replace with SDK calls when endpoint is ready)
└── styles/
    └── globals.css     ← Tailwind directives + CSS design token definitions
```

## Adding a New Page

1. Create the page in the appropriate subdirectory:

```jsx
// src/pages/account/NewPage.jsx  (or admin/..., shopping/..., etc.)
export default function NewPage() {
  return <div>{/* content */}</div>;
}
```

2. Register a `<Route>` in `src/App.jsx` inside the correct layout group:

```jsx
import NewPage from "./pages/account/NewPage";
// ...
// Inside the CustomerRoute → AccountLayout block:
<Route path='/account/new' element={<NewPage />} />;
```

Pages always belong in a subdirectory (`account/`, `admin/catalog/`, `shopping/`, `auth/`, `storefront/`) — never flat in `pages/`.

## Adding a New Component

Place in the correct subdirectory:

| Component type                             | Location                              |
| ------------------------------------------ | ------------------------------------- |
| Generic UI primitive (button, input, card) | `src/components/ui/<category>/`       |
| Cart-specific                              | `src/components/cart/`                |
| Wishlist-specific                          | `src/components/wishlist/`            |
| Layout (header, footer, sidebar)           | `src/components/layout/`              |
| Product display                            | `src/components/products/`            |
| Order display                              | `src/components/orders/`              |
| Review display                             | `src/components/reviews/`             |
| Notification display                       | `src/components/notifications/`       |
| Inventory display                          | `src/components/inventory/`           |
| Report display                             | `src/components/reports/`             |
| Route guards                               | `src/components/guards/`              |
| Admin-specific (shared across admin pages) | `src/components/admin/`               |
| Account-specific (shared across account)   | `src/components/account/`             |
| Page-specific (used in one page only)      | keep it inside `src/pages/<section>/` |

File naming: lowercase kebab-case (`product-card.jsx`, not `ProductCard.jsx`).

Export convention: named export for shared components, default export for pages.

## Class Merging — Always Use `cn()`

`src/lib/utils.js` exports `cn()` combining `clsx` + `tailwind-merge`.
Always use it when conditionally applying or combining Tailwind classes:

```jsx
import { cn } from "@/lib/utils";

<div className={cn("base-classes", isActive && "active-class", className)} />;
```

Never concatenate class strings manually.

## Variant Components — Use `cva`

For components with multiple visual variants, follow the pattern in
`src/components/ui/forms/button.jsx`:

```jsx
import { cva } from "class-variance-authority";
import { cn } from "@/lib/utils";

const cardVariants = cva("rounded-md transition-colors", {
  variants: {
    variant: { default: "bg-primary text-primary-foreground", outline: "border border-border" },
    size: { sm: "px-3 py-1.5 text-sm", default: "px-4 py-2", lg: "px-6 py-3" },
  },
  defaultVariants: { variant: "default", size: "default" },
});

export function Card({ className, variant, size, asChild = false, ...props }) {
  const Comp = asChild ? Slot : "div";
  return <Comp className={cn(cardVariants({ variant, size, className }))} {...props} />;
}
```

Use Radix `Slot` for polymorphic components that need to render as a different element.

## API Calls — Use the Generated SDK Client

**Do not use raw `fetch()` for new API calls.** Use `@bukoo/api-client`.

Configured instances live in `src/lib/apiClient.js`:

```jsx
import { AuthApi, Configuration } from "@bukoo/api-client";
import Cookies from "js-cookie";

const configuration = new Configuration({
  basePath: "", // Vite proxy handles /api/* → :8000
  middleware: [
    {
      pre: async (ctx) => ({
        ...ctx,
        init: {
          ...ctx.init,
          headers: {
            ...ctx.init.headers,
            ...(Cookies.get("jwt") ? { Authorization: `Bearer ${Cookies.get("jwt")}` } : {}),
          },
        },
      }),
    },
  ],
});

export const authApi = new AuthApi(configuration);
```

To use a new backend endpoint:

1. Add the route to the backend
2. Run `make generate-sdk` from the repo root
3. Add a configured instance in `src/lib/apiClient.js`
4. Call it from a component or action file

Note: `src/actions/auth.js` uses raw `fetch()` — this is legacy and should be
migrated to the SDK client as the auth flow stabilises.

## Authentication

`AuthContext` (`src/context/AuthContext.jsx`) provides `{ user, loading, login, logout }`.

- JWT stored in `js-cookie` under key `jwt`
- `loading` is `true` on initial mount while the stored token is validated
- Access via `useAuth()` hook

To protect a route:

```jsx
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";

export default function ProtectedPage() {
  const { user, loading } = useAuth();
  if (loading) return <div>Loading…</div>;
  if (!user) return <Navigate to='/login' replace />;
  return <PageLayout>…</PageLayout>;
}
```

## Design Tokens

CSS custom properties are defined in `src/styles/globals.css`. Colors use HSL
values **without** the `hsl()` wrapper — this is required for Tailwind's opacity
modifier syntax (`bg-primary/50`) to work:

```css
/* ✓ correct */
--primary: 31 85% 13%;
--background: 0 0% 96%;
--border: 45 28% 81%;

/* ✗ wrong — breaks opacity modifiers */
--primary: hsl(31 85% 13%);
```

Typography:

- `font-serif` → EB Garamond (editorial headings, book titles)
- `font-sans` → Inter (body text, UI)

Custom spacing: `px-sides` applies `var(--padding-sides)` (2rem). Use for
consistent horizontal page padding.

## Context Provider Order

The provider order in `App.jsx` is outer → inner:

```
AuthProvider → CartProvider → WishlistProvider → BrowserRouter
```

Add new context providers between `WishlistProvider` and `BrowserRouter` unless
they need to wrap auth/cart/wishlist (rare).

## Current Routes

Routes are organized into four layout groups in `App.jsx`.

**Auth layout** (no header/footer):

| Path                         | Page                       |
| ---------------------------- | -------------------------- |
| `/login`                     | LoginPage                  |
| `/register`                  | RegisterPage               |
| `/oauth/callback`            | OAuthCallbackPage          |
| `/verify-email`              | VerifyEmailPage            |
| `/forgot-password`           | ForgotPasswordPage         |
| `/verify-password-reset-otp` | VerifyPasswordResetOtpPage |
| `/reset-password`            | ResetPasswordPage          |

**Storefront layout** (header + footer, public):

| Path                | Page              | Notes                  |
| ------------------- | ----------------- | ---------------------- |
| `/`                 | HomePage          | Landing page           |
| `/shop`             | ShopPage          | All books              |
| `/shop/:collection` | ShopPage          | Filtered by collection |
| `/search`           | ShopPage          | Search results         |
| `/product/:handle`  | ProductDetailPage | Custom header variant  |

**Customer layout** (requires customer role; admins redirected to `/admin`):

| Path                       | Page                     |
| -------------------------- | ------------------------ |
| `/account`                 | AccountPage              |
| `/account/profile`         | ProfilePage              |
| `/account/password`        | PasswordPage             |
| `/account/address`         | AddressPage              |
| `/account/wishlist`        | WishlistPage             |
| `/account/delete`          | DeleteAccountPage        |
| `/account/orders`          | AccountOrdersPage        |
| `/account/orders/:orderId` | AccountOrderDetailPage   |
| `/account/reviews`         | AccountReviewsPage       |
| `/account/notifications`   | AccountNotificationsPage |
| `/account/cart`            | CartPage                 |
| `/checkout`                | CheckoutPage             |
| `/checkout/payment`        | CheckoutPaymentPage      |
| `/checkout/confirmation`   | CheckoutConfirmationPage |

**Admin layout** (requires admin role):

| Path                               | Page                   |
| ---------------------------------- | ---------------------- |
| `/admin`                           | AdminDashboardPage     |
| `/admin/notifications`             | AdminNotificationsPage |
| `/admin/books`                     | BooksPage              |
| `/admin/books/new`                 | BookNewPage            |
| `/admin/books/:bookId`             | BookDetailPage         |
| `/admin/collections`               | CollectionsPage        |
| `/admin/collections/new`           | CollectionNewPage      |
| `/admin/collections/:collectionId` | CollectionDetailPage   |
| `/admin/categories`                | CategoriesPage         |
| `/admin/categories/new`            | CategoryNewPage        |
| `/admin/categories/:categoryId`    | CategoryDetailPage     |
| `/admin/authors`                   | AuthorsPage            |
| `/admin/authors/new`               | AuthorNewPage          |
| `/admin/authors/:authorId`         | AuthorDetailPage       |
| `/admin/publishers`                | PublishersPage         |
| `/admin/publishers/new`            | PublisherNewPage       |
| `/admin/publishers/:publisherId`   | PublisherDetailPage    |
| `/admin/users`                     | UsersPage              |
| `/admin/users/new`                 | UserNewPage            |
| `/admin/users/:userId`             | UserDetailPage         |
| `/admin/orders`                    | AdminOrdersPage        |
| `/admin/orders/:orderId`           | AdminOrderDetailPage   |
| `/admin/reviews`                   | AdminReviewsPage       |
| `/admin/inventory`                 | InventoryPage          |
| `/admin/reports`                   | ReportsPage            |

**Fallback:** `*` → NotFoundPage

## Forms

React Hook Form + Zod for all forms:

```jsx
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const schema = z.object({ email: z.string().email(), password: z.string().min(8) });

export function LoginForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
  });
  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register("email")} />
      {errors.email && <p>{errors.email.message}</p>}
    </form>
  );
}
```

Wrap fields with `src/components/ui/forms/field.jsx` for consistent label + error layout.

## Notifications / Toast

Use `sonner` for toast notifications. `<Toaster>` is already mounted in `App.jsx`:

```jsx
import { toast } from "sonner";

toast.success("Item added to cart");
toast.error("Something went wrong");
```

Do not use the Radix-based toast in `src/components/ui/feedback/` for new work —
`sonner` is the active pattern.

## 3D Book Visualization

`src/components/3d-book/` uses React Three Fiber + `@react-three/drei`.
The 3D model is loaded from `public/`. Do not:

- Move or rename files in `public/` without updating the loader path
- Add Three.js/R3F code outside of `src/components/3d-book/`

Import `BookViewer3D` (or the appropriate export) as the single entry point.

## Mock Data

`src/data/mock/` contains JSON fixtures for any UI that hasn't been wired to a
real backend endpoint yet. Most endpoints are now implemented — only replace a
mock import with an SDK call once the corresponding endpoint is confirmed working.
Delete the mock file after migration.

## Testing

Frontend uses Vitest + @testing-library/react. Tests are co-located next to the
file they test (`component.test.jsx`, `hook.test.js`).

```bash
cd frontend && pnpm test           # Vitest watch mode
cd frontend && pnpm test:unit      # run once (components + hooks only)
cd frontend && pnpm test:coverage  # with coverage report
```

The root `make test*` targets run backend pytest only — they do not run frontend tests.

## Quality Checks

Run before every frontend commit:

```bash
make fe-check    # ESLint + Prettier check (read-only)
make fe-format   # auto-fix ESLint issues + Prettier (writes files)
```

ESLint and Prettier are configured in `frontend/eslint.config.mjs` and
`frontend/.prettierrc`. Do not add duplicate config files.

## Environment Variables

Vite exposes `VITE_*` vars via `import.meta.env.VITE_*`:

```
VITE_SITE_URL=http://localhost:5173   # used by src/lib/utils.js baseUrl
```

Create `frontend/.env.local` for local overrides (gitignored).
