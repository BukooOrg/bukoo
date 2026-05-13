# Verify Password Reset Page Proposal

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **API Endpoint** | `GET /api/app/v1/auth/password/reset/verify` (API 1.8) |
| **Route** | `/verify-password-reset?email=<email>&otp=<otp>` |
| **Access Level** | 🌐 Public |
| **Priority** | High |
| **Status** | Proposal — Ready for review |

---

## User Flow

```
User clicks reset link in email
                ↓
   /verify-password-reset?email=<email>&otp=<otp>
                ↓
   Auto-verify token with API
                ↓
   ┌─────────────┴─────────────┐
   │                           │
   ▼                           ▼
Valid Token              Invalid/Expired Token
   │                           │
   ▼                           ▼
Redirect to              Show error message
/reset-password          "Request new reset link"
                         Resend link button
```

---

## UI Wireframe Description

### Layout Structure

- **Container**: Full-screen centered layout (matches other auth pages)
- **Card**: White/80 backdrop blur, rounded-40px, shadow-2xl
- **Background**: Abstract blur gradients (top-left, bottom-right)
- **Content**: Vertically centered with proper spacing

### Visual Elements

1. **Icon Section** (top center)
   - Circular icon container (bg-primary/5)
   - Lucide icon: `ShieldCheck` or `Key` (w-7 h-7, text-primary)

2. **Title Section**
   - H1: "Verifying Reset Link" (font-serif, text-5xl, font-black, text-primary)
   - Subtitle: "Please wait while we verify your password reset link" (text-sm, italic, text-primary/40)

3. **Loading State**
   - Large spinner (Loader2, w-12 h-12, text-primary)
   - Centered in card
   - No other content visible

4. **Success State**
   - CheckCircle icon (green, w-16 h-16)
   - Message: "Reset link verified! Redirecting to password reset..."
   - Auto-redirect after 2 seconds
   - Manual "Continue" link (in case redirect fails)

5. **Error State**
   - AlertCircle icon (destructive, w-16 h-16)
   - Message: "This reset link is invalid or has expired"
   - "Request New Reset Link" button
   - "Back to Login" link

---

## Component Tree

```
VerifyPasswordResetPage (default export)
├── AuthLayout (route wrapper from App.jsx)
├── VerificationCard
│   ├── IconSection
│   │   └── ShieldCheck icon (lucide-react)
│   ├── TitleSection
│   │   ├── H1 title
│   │   └── Subtitle paragraph
│   ├── LoadingState (conditional)
│   │   └── Large spinner
│   ├── SuccessState (conditional)
│   │   ├── CheckCircle icon
│   │   ├── Success message
│   │   └── ContinueButton
│   └── ErrorState (conditional)
│       ├── AlertCircle icon
│       ├── Error message
│       ├── RequestNewLinkButton
│       └── BackToLogin link
└── Toaster (from sonner)
```

---

## State Requirements

### Local State (useState)

| State | Type | Initial | Purpose |
|-------|------|---------|---------|
| `status` | 'loading' \| 'success' \| 'error' | 'loading' | Current verification status |
| `error` | string | `''` | Error message to display |
| `email` | string | `''` | Email from URL param |
| `otp` | string | `''` | OTP from URL param |

### URL Query Parameters

| Param | Type | Required | Purpose |
|-------|------|----------|---------|
| `email` | string | Yes | User's email address |
| `otp` | string | Yes | Reset verification token |

---

## API Integration

### SDK Method Call

```javascript
import { authApi } from '@/lib/apiClient';
import { useApiQuery } from '@/hooks/useApiQuery';

const { data, loading, error } = useApiQuery(
  () => authApi.verifyPasswordReset({ email, otp }),
  {
    skip: !email || !otp,
  }
);

// On success: redirect to /reset-password?email=<email>
// On error: show error state
```

---

## Loading States

### Initial Load

- Check for `email` and `otp` in URL
- If missing: show error immediately
- If present: auto-verify with API
- Show large spinner during verification

### During Verification

- Spinner centered
- No other interactive elements
- Background dimmed slightly

---

## Error States

### Missing URL Parameters

**Trigger:** No `email` or `otp` in URL

**UI Response:**
- Error state immediately
- Message: "Invalid reset link. Please request a new one."
- "Request New Reset Link" button
- "Back to Login" link

---

### Invalid/Expired Token (API 400)

**Error Code:** `INVALID_OTP` or `OTP_EXPIRED`

**UI Response:**
- Error state
- Message: "This reset link is invalid or has expired"
- "Request New Reset Link" button
- "Back to Login" link

---

### User Not Found (API 404)

**Error Code:** `USER_NOT_FOUND`

**UI Response:**
- Error state
- Message: "No account found with this email address"
- "Back to Login" link

---

### Network Error

**UI Response:**
- Error state
- Message: "Could not connect to server. Please check your connection and try again."
- Retry button

---

## Storybook Stories

### VerifyPasswordResetPage.stories.jsx

```javascript
import VerifyPasswordResetPage from './VerifyPasswordResetPage';

export default {
  title: 'Auth/VerifyPasswordResetPage',
  component: VerifyPasswordResetPage,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Loading = {
  args: {
    status: 'loading',
    email: 'user@example.com',
    otp: '123456',
  },
};

export const Success = {
  args: {
    status: 'success',
    email: 'user@example.com',
    otp: '123456',
  },
};

export const InvalidToken = {
  args: {
    status: 'error',
    error: 'This reset link is invalid or has expired',
    email: 'user@example.com',
    otp: 'wrong-token',
  },
};

export const MissingParams = {
  args: {
    status: 'error',
    error: 'Invalid reset link. Please request a new one.',
    email: '',
    otp: '',
  },
};

export const NetworkError = {
  args: {
    status: 'error',
    error: 'Could not connect to server',
    email: 'user@example.com',
    otp: '123456',
  },
};
```

---

## Accessibility (A11y) Considerations

### Keyboard Navigation

- **Tab**: Move between buttons (error state only)
- **Enter**: Activate focused button
- **Escape**: Navigate back to login

### Screen Reader Support

- Loading state: `aria-live="polite"` with "Verifying reset link"
- Success state: `aria-live="assertive"` with "Reset link verified"
- Error state: `role="alert"` with error message
- All buttons have descriptive labels

### Focus Management

- Auto-focus "Request New Reset Link" button on error
- Auto-focus "Continue" button on success
- Move focus to error message on error

---

## Responsive Design

### Mobile (< 768px)

- Card padding: p-6
- Reduced font sizes: text-4xl for title
- Icon sizes: w-12 h-12
- Full-width buttons

### Desktop (≥ 768px)

- Card padding: p-10 md:p-12
- Full font sizes: text-5xl for title
- Icon sizes: w-16 h-16
- Standard button width

---

## Design Tokens Used

### Colors

```css
--primary: 31 85% 13%        /* Main brand color */
--secondary: 0 0% 96%        /* Button text */
--destructive: 0 84% 60%     /* Error states */
--background: 0 0% 96%       /* Page background */
--success: 142 76% 36%       /* Success state (green) */
```

### Typography

```
font-serif: EB Garamond      /* Headings */
font-sans: Inter             /* Body text, inputs */
```

---

## Edge Cases & Brainstorming

### 1. User Opens Link in New Tab After Already Used

**Behavior:**
- Token is already invalidated
- Show error: "This reset link has already been used"
- "Request New Reset Link" button

---

### 2. User Edits URL Parameters Manually

**Behavior:**
- Invalid email/otp format
- API returns 400
- Show error state
- No special handling needed

---

### 3. User Navigates Back After Success

**Behavior:**
- Success state is lost (local state)
- Page shows loading again
- API call happens again
- Consider storing verification status in sessionStorage (not in v1)

---

### 4. Slow Network Connection

**Behavior:**
- Spinner shows indefinitely
- No timeout (wait for API response)
- User can't retry until response received

**Enhancement (v2):**
- Add timeout after 30 seconds
- Show "Request timed out. Please try again."

---

## Acceptance Criteria

### Functional Requirements

- [ ] Auto-verify token on page load
- [ ] Show loading state during verification
- [ ] Redirect to /reset-password on success
- [ ] Show error state on failure
- [ ] "Request New Reset Link" button works
- [ ] "Back to Login" link works
- [ ] Handle missing URL parameters

### Visual Requirements

- [ ] Matches LoginPage design style
- [ ] Responsive on mobile and desktop
- [ ] Loading states visible
- [ ] Error states clearly indicated
- [ ] Success state with animation

### Accessibility Requirements

- [ ] Keyboard navigation works
- [ ] Screen reader announces states
- [ ] Focus management correct
- [ ] ARIA labels present

### Quality Requirements

- [ ] ESLint passes
- [ ] Prettier formatted
- [ ] Storybook stories render
- [ ] No console errors

---

## Files to Create/Modify

| File | Action | Description |
|------|--------|-------------|
| `frontend/src/pages/auth/VerifyPasswordResetPage.jsx` | Modify | Full implementation (currently skeleton) |
| `frontend/src/pages/auth/VerifyPasswordResetPage.stories.jsx` | Create | Storybook stories |

---

## Implementation Notes

### Do's

- ✅ Use `useApiQuery` hook for API call
- ✅ Use `cn()` for class merging
- ✅ Use Lucide React icons consistently
- ✅ Follow existing LoginPage design patterns
- ✅ Use `toast` from sonner for notifications
- ✅ Use `useSearchParams` for URL params
- ✅ Auto-redirect on success

### Don'ts

- ❌ Don't use raw `fetch()` — use SDK client
- ❌ Don't concatenate class strings — use `cn()`
- ❌ Don't use hardcoded colors — use design tokens
- ❌ Don't show OTP input (this is verification only)
- ❌ Don't allow retry without requesting new link

---

## Definition of Done

- [ ] Proposal reviewed and approved
- [ ] Page component implemented
- [ ] Storybook stories created
- [ ] API integration complete
- [ ] All error states handled
- [ ] Accessibility tested
- [ ] Responsive design verified
- [ ] ESLint/Prettier passing
- [ ] Manual testing completed
- [ ] Committed with conventional commit message

---

**Next Steps:**
1. Review this proposal
2. Approve or request changes
3. Implement following this specification
4. Test all acceptance criteria
