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
├── actions/            ← thin API call wrappers (no state management)
├── components/
│   ├── 3d-book/        ← Three.js / R3F 3D book visualization
│   ├── cart/           ← cart context, cart modal, add-to-cart button
│   ├── layout/         ← header, footer, page-layout wrapper
│   ├── products/       ← product cards, variant selector
│   └── ui/             ← design system primitives
│       ├── forms/      ← button, input, field, select, checkbox
│       ├── feedback/   ← spinner, skeleton, alert, badge
│       ├── data-display/ ← table, list, card
│       ├── navigation/ ← tabs, breadcrumbs, pagination
│       ├── overlays/   ← dialog, sheet, tooltip, popover
│       └── misc/       ← separator, scroll-area, aspect-ratio
├── context/            ← React context providers (auth, cart)
├── hooks/              ← custom React hooks
├── lib/                ← utilities, API client instances, constants
├── pages/              ← route-level page components
├── data/mock/          ← temporary mock JSON (replace with SDK calls as backend grows)
└── styles/
    └── globals.css     ← Tailwind directives + CSS design token definitions
```

## Adding a New Page

1. Create `src/pages/<PageName>.jsx`:

```jsx
import { PageLayout } from "@/components/layout/page-layout";

export default function PageName() {
  return <PageLayout>{/* content */}</PageLayout>;
}
```

2. Register a `<Route>` in `src/App.jsx`:

```jsx
import PageName from "./pages/PageName";
// ...
<Route path='/your-path' element={<PageName />} />;
```

## Adding a New Component

Place in the correct subdirectory:

| Component type                             | Location                           |
| ------------------------------------------ | ---------------------------------- |
| Generic UI primitive (button, input, card) | `src/components/ui/<category>/`    |
| Cart-specific                              | `src/components/cart/`             |
| Layout (header, footer, sidebar)           | `src/components/layout/`           |
| Product display                            | `src/components/products/`         |
| Page-specific (used in one page only)      | keep it inside `src/pages/<Page>/` |

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
AuthProvider → CartProvider → BrowserRouter
```

Add new context providers between `CartProvider` and `BrowserRouter` unless
they need to wrap auth/cart (rare).

## Current Routes

| Path                | Component     | Notes                     |
| ------------------- | ------------- | ------------------------- |
| `/`                 | Home          | Landing page              |
| `/shop`             | Shop          | All books                 |
| `/shop/:collection` | Shop          | Filtered by collection    |
| `/search`           | Shop          | Search results            |
| `/product/:handle`  | ProductDetail | Book detail page          |
| `/login`            | Login         | Auth                      |
| `/register`         | Register      | Auth                      |
| `*`                 | 404 inline    | "404 - Chapter Not Found" |

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

`src/data/mock/products.json` and `collections.json` are used while the backend
product/collection endpoints are not yet implemented. When a real endpoint is
available, replace the mock import with a call to the appropriate SDK client
instance and delete the mock file.

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
