# Frontend Feature Checklist

## Auth Pages (7 pages)

- [x] **LoginPage** — Email/password login, Google/Facebook OAuth, "Forgot Password?" link
- [x] **RegisterPage** — Full name, email, DOB, password + confirm, password strength meter
- [x] **VerifyEmailPage** — 6-digit OTP input, auto-verify from URL token, resend with cooldown
- [x] **ForgotPasswordPage** — Email input, sends reset code, auto-redirects to OTP page
- [x] **VerifyPasswordResetOtpPage** — 6-digit OTP input, resend with cooldown, redirects to reset
- [x] **ResetPasswordPage** — New password + confirm, strength meter, visibility toggle
- [x] **OAuthCallbackPage** — Handles OAuth redirect from backend

## Auth Components (3 components)

- [x] **OtpInput** — 6-digit OTP input with auto-advance, paste, backspace
- [x] **OtpInputBox** — Single digit input box
- [x] **PasswordStrengthMeter** — 3-level (Weak/Medium/Strong) indicator

## Auth Hooks (2 hooks)

- [x] **useApiQuery** — Generic query hook with loading, error, skip, cancel
- [x] **useApiMutation** — Generic mutation hook with loading, error, callbacks

## Storefront Pages (4 pages)

- [x] **HomePage** — Featured products grid (uses mock `@/lib/sfcc` data, not backend API)
- [x] **ShopPage** — Product grid with collection filter and search (uses mock `@/lib/sfcc` data)
- [x] **ProductDetailPage** — Book detail with 2D/3D viewer, add-to-cart, variants (uses mock `@/lib/sfcc` data)
- [x] **NotFoundPage** — 404 page (minimal)

## Shopping Pages (5 pages) — ALL PLACEHOLDERS

- [ ] **CartPage** — 5-line placeholder
- [ ] **CheckoutPage** — 5-line placeholder
- [ ] **CheckoutPaymentPage** — 5-line placeholder
- [ ] **CheckoutConfirmationPage** — 5-line placeholder
- [ ] **WishlistPage** — 5-line placeholder

## Account Pages (9 pages) — ALL PLACEHOLDERS

- [ ] **AccountPage** — 5-line placeholder
- [ ] **ProfilePage** — 5-line placeholder
- [ ] **PasswordPage** — 5-line placeholder
- [ ] **AddressPage** — 5-line placeholder
- [ ] **OrdersPage** — 5-line placeholder
- [ ] **OrderDetailPage** — 5-line placeholder
- [ ] **ReviewsPage** — 5-line placeholder
- [ ] **NotificationsPage** — 5-line placeholder
- [ ] **DeleteAccountPage** — 5-line placeholder

## Admin Pages (21 pages) — ALL PLACEHOLDERS

- [ ] **DashboardPage** — 5-line placeholder
- [ ] **NotificationsPage** — 5-line placeholder
- [ ] **BooksPage** — 5-line placeholder
- [ ] **BookNewPage** — 5-line placeholder
- [ ] **BookDetailPage** — 5-line placeholder
- [ ] **CollectionsPage** — 5-line placeholder
- [ ] **CollectionDetailPage** — 5-line placeholder
- [ ] **CategoriesPage** — 5-line placeholder
- [ ] **CategoryDetailPage** — 5-line placeholder
- [ ] **AuthorsPage** — 5-line placeholder
- [ ] **AuthorDetailPage** — 5-line placeholder
- [ ] **PublishersPage** — 5-line placeholder
- [ ] **PublisherDetailPage** — 5-line placeholder
- [ ] **UsersPage** — 5-line placeholder
- [ ] **UserNewPage** — 5-line placeholder
- [ ] **UserDetailPage** — 5-line placeholder
- [ ] **OrdersPage** — 5-line placeholder
- [ ] **OrderDetailPage** — 5-line placeholder
- [ ] **ReviewsPage** — 5-line placeholder
- [ ] **InventoryPage** — 5-line placeholder
- [ ] **ReportsPage** — 5-line placeholder

## Layout & Guards (6 components)

- [x] **AuthLayout** — No header/footer for auth pages
- [x] **StorefrontLayout** — Header + footer for storefront
- [x] **AdminLayout** — Sidebar shell for admin
- [x] **ProtectedRoute** — Requires any authenticated user
- [x] **CustomerRoute** — Requires customer role
- [x] **AdminRoute** — Requires admin role

## Shared Components

- [x] **Header** — Site navigation
- [x] **Footer** — Site footer
- [x] **PageLayout** — Generic page wrapper
- [x] **CartContext** — Cart state management
- [x] **AuthContext** — Auth state management
- [x] **AddToCart** — Add to cart button
- [x] **3D Book Viewer** — Three.js book visualization
- [x] **Prose** — HTML content renderer
- [x] **Breadcrumb** — Navigation breadcrumbs
- [x] **LatestProductCard** — Product card (mock data)
- [ ] **ProductCard** — Reusable product card (backend API)
- [ ] **VariantSelector** — Book variant picker
- [ ] **DesktopGallery** — Product image gallery (exists but tied to mock data)
- [ ] **MobileGallerySlider** — Mobile image gallery (exists but tied to mock data)
- [ ] **UI Primitives** — Button, Input, Field, Select, Checkbox, Spinner, Skeleton, Alert, Badge, Table, List, Card, Tabs, Breadcrumbs, Pagination, Dialog, Sheet, Tooltip, Popover, Separator, ScrollArea, AspectRatio

## Testing

- [x] **Unit Tests** — Components (OtpInput, OtpInputBox, PasswordStrengthMeter)
- [x] **Unit Tests** — Hooks (useApiQuery, useApiMutation)
- [x] **Unit Tests** — AuthContext
- [x] **Integration Tests** — Auth pages (Login, Register, Verify, Forgot, Reset)
- [ ] **E2E Tests** — Skipped (Playwright not required)

## Infrastructure

- [x] **Vite Dev Server** — Running on :5173
- [x] **Vite Proxy** — `/api/*` → `http://localhost:8000`
- [x] **Storybook** — Component documentation
- [x] **ESLint + Prettier** — Code quality
- [x] **Tailwind CSS** — Styling with design tokens
- [x] **React Router** — Route management
- [x] **Sonner Toast** — Notifications
- [x] **Vitest** — Config exists (vitest.config.js)

## SDK Integration

- [x] **@bukoo/api-client** — Auto-generated SDK client
- [x] **Auth API calls** — All auth endpoints use SDK
- [ ] **Product API calls** — Browse, search, product detail (currently uses mock `@/lib/sfcc`)
- [ ] **Cart API calls** — Add, remove, update cart
- [ ] **Checkout API calls** — Order creation, payment
- [ ] **Account API calls** — Profile, address, orders, reviews
- [ ] **Admin API calls** — All admin endpoints

## Summary

| Category | Implemented | Placeholders | Total |
|----------|-------------|--------------|-------|
| Auth Pages | 7 | 0 | 7 |
| Auth Components | 3 | 0 | 3 |
| Auth Hooks | 2 | 0 | 2 |
| Storefront Pages | 3 (mock data) | 1 | 4 |
| Shopping Pages | 0 | 5 | 5 |
| Account Pages | 0 | 9 | 9 |
| Admin Pages | 0 | 21 | 21 |
| Layout & Guards | 6 | 0 | 6 |
| Shared Components | ~10 | ~20 | ~30 |
| Testing | 4 suites ✅ | 0 | 4 |
| SDK Integration | 2 | 5 | 7 |

**Total pages implemented:** 10 of 46 (22%)
**Total pages with real content:** 7 auth + 3 storefront (mock data) = 10
**Total placeholder pages:** 36
