# Forgot Password Page Proposal

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **API Endpoint** | `POST /api/app/v1/auth/password/forgot` (API 1.7) |
| **Route** | `/forgot-password` |
| **Access Level** | 🌐 Public |
| **Priority** | High |
| **Status** | Proposal — Ready for review |

---

## User Flow

```
User clicks "Forgot Password?" link on login page
                ↓
         ForgotPasswordPage
                ↓
    Enter email address → Submit
                ↓
    API sends reset OTP to email
                ↓
    Show success message
                ↓
    Option 1: Auto-redirect to /verify-password-reset
    Option 2: Manual navigation to reset page
                ↓
    User receives email with OTP
                ↓
    Navigate to /verify-password-reset?email=<email>
```

---

## UI Wireframe Description

### Layout Structure

- **Container**: Full-screen centered layout (matches LoginPage/RegisterPage style)
- **Card**: White/80 backdrop blur, rounded-40px, shadow-2xl
- **Background**: Abstract blur gradients (top-left, bottom-right)
- **Content**: Vertically centered with proper spacing

### Visual Elements

1. **Icon Section** (top center)
   - Circular icon container (bg-primary/5)
   - Lucide icon: `Key` or `Lock` (w-7 h-7, text-primary)

2. **Title Section**
   - H1: "Forgot Password?" (font-serif, text-5xl, font-black, text-primary)
   - Subtitle: "Enter your email and we'll send you reset instructions" (text-sm, italic, text-primary/40)

3. **Email Input Field**
   - Full-width input with icon (Mail icon on left)
   - Label: "Email Address" (uppercase, tracking-widest, text-xs)
   - Placeholder: "Enter your email address"
   - Validation: Real-time email format check

4. **Submit Button**
   - Full-width, py-5, bg-primary, text-secondary
   - Loading state: spinner icon
   - Disabled during submission
   - Icon: `Send` or `Mail`

5. **Success State** (after submission)
   - CheckCircle icon (green)
   - Success message: "Check your inbox! We've sent password reset instructions to {email}"
   - "Didn't receive email?" → Resend button
   - "Back to Login" link

6. **Back to Login Link**
   - Positioned below card with mt-20
   - Arrow left icon + "Back to Login" text
   - Uppercase, tracking-widest

---

## Component Tree

```
ForgotPasswordPage (default export)
├── AuthLayout (route wrapper from App.jsx)
├── ForgotPasswordCard
│   ├── IconSection
│   │   └── Key icon (lucide-react)
│   ├── TitleSection
│   │   ├── H1 title
│   │   └── Subtitle paragraph
│   ├── EmailForm
│   │   ├── Field label
│   │   ├── EmailInput (with Mail icon)
│   │   ├── SubmitButton
│   │   │   ├── Loader2 (loading state)
│   │   │   └── Send icon
│   │   └── ErrorMessage (if any)
│   ├── SuccessState (conditional)
│   │   ├── CheckCircle icon
│   │   ├── Success message
│   │   ├── ResendButton
│   │   └── BackToLogin link
│   └── BackToHome (Link component)
└── Toaster (from sonner)
```

---

## State Requirements

### Local State (useState)

| State | Type | Initial | Purpose |
|-------|------|---------|---------|
| `email` | string | `''` | Email input value |
| `isSubmitting` | boolean | `false` | Submission in progress |
| `error` | string | `''` | Error message to display |
| `success` | boolean | `false` | Email sent successfully |
| `isResending` | boolean | `false` | Resend in progress |
| `cooldown` | number | `0` | Seconds until resend available |

### URL Query Parameters

| Param | Type | Required | Purpose |
|-------|------|----------|---------|
| `email` | string | No | Pre-fill email (from previous flow) |

### Form Validation

| Field | Rules | Error Messages |
|-------|-------|----------------|
| `email` | Required, valid email format | "Please enter a valid email address" |

---

## Form Schema (Zod)

```javascript
import { z } from 'zod';

export const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address'),
});

export type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;
```

---

## New Components Needed

### None (Reuse Existing)

All components already exist:
- **Email Input**: Use standard input component with Mail icon
- **Field Wrapper**: Use existing `Field` component from `src/components/ui/forms/`
- **Button**: Use existing `Button` component with variants
- **Icons**: Lucide React (`Key`, `Mail`, `Send`, `CheckCircle`, `Loader2`)

---

## API Integration

### SDK Method Call

```javascript
import { authApi } from '@/lib/apiClient';
import { useApiMutation } from '@/hooks/useApiMutation';

const { mutate: forgotPassword, loading: isSubmitting, error: apiError } = useApiMutation(
  (variables) => authApi.forgotPassword(variables),
  {
    onSuccess: (data) => {
      setSuccess(true);
      toast.success('Password reset email sent! Check your inbox.');
      // Optionally start cooldown for resend
      setCooldown(30);
    },
    onError: (err) => {
      const message = err.response?.data?.error?.message || 'Failed to send reset email';
      setError(message);
    },
  }
);

// Usage:
forgotPassword({ forgotPasswordRequest: { email } });
```

### Resend API (Same Endpoint)

```javascript
const { mutate: resendResetEmail, loading: isResending } = useApiMutation(
  (variables) => authApi.forgotPassword(variables),
  {
    onSuccess: () => {
      toast.success('Reset email resent!');
      setCooldown(30);
    },
  }
);
```

---

## Loading States

### Initial State

- Email input enabled
- Submit button enabled (when email is valid)
- No loading indicators

### During Submission

- Submit button shows spinner (Loader2 icon)
- Button text: "Sending..."
- Email input disabled
- No other loading indicators

### Success State

- Form hidden
- CheckCircle icon appears (green, animated)
- Success message displayed
- "Resend" button available (with cooldown)
- "Back to Login" link visible

---

## Error States

### Invalid Email Format (Client-side)

**Trigger:** Email doesn't match pattern

**UI Response:**
- Field-level error below email input
- Input border turns red (border-destructive)
- Error message: "Please enter a valid email address"

---

### Email Not Found (API 404)

**Error Code:** `USER_NOT_FOUND`

**UI Response:**
- Full error message below submit button
- Error style: border-destructive/10 bg-destructive/5
- Message: "No account found with this email address"
- Suggestion: "Check your email or create a new account"

**Security Note:** For security, consider showing generic success even if email not found (prevents email enumeration). Decision: Show error for better UX.

---

### Email Already Verified + No Password (OAuth User)

**Error Code:** `USER_NO_PASSWORD`

**UI Response:**
- Full error message
- Message: "This account uses social login. Please sign in with your connected provider."
- Link to login page

---

### Rate Limit Exceeded (API 429)

**Error Code:** `RATE_LIMIT_EXCEEDED`

**UI Response:**
- Full error message
- Message: "Too many attempts. Please try again in {retry_after} seconds"
- Disable submit button for duration

---

### Network Error

**UI Response:**
- Generic error message
- Message: "Could not connect to server. Please check your connection and try again."
- Retry button

---

## Storybook Stories

### ForgotPasswordPage.stories.jsx

```javascript
import ForgotPasswordPage from './ForgotPasswordPage';

export default {
  title: 'Auth/ForgotPasswordPage',
  component: ForgotPasswordPage,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Default = {
  args: {},
};

export const WithPrefilledEmail = {
  args: {
    email: 'user@example.com',
  },
};

export const Submitting = {
  args: {
    isSubmitting: true,
    email: 'user@example.com',
  },
};

export const Success = {
  args: {
    success: true,
    email: 'user@example.com',
  },
};

export const Error = {
  args: {
    error: 'No account found with this email address',
    email: 'nonexistent@example.com',
  },
};

export const ResendCooldown = {
  args: {
    success: true,
    email: 'user@example.com',
    cooldown: 25,
  },
};
```

---

## Accessibility (A11y) Considerations

### Keyboard Navigation

- **Tab**: Move between email input and submit button
- **Enter**: Submit form
- **Escape**: Navigate back to login

### Screen Reader Support

- Email input has `aria-label="Email address"`
- Error messages use `role="alert"`
- Success message announces "Password reset email sent"
- Loading state: `aria-busy="true"` on submit button
- Success state: `aria-live="polite"` on success message

### Focus Management

- Auto-focus email input on page load
- Move focus to success message after submission
- Restore focus after error

---

## Responsive Design

### Mobile (< 768px)

- Card padding: p-6
- Reduced font sizes: text-4xl for title
- Input/button padding: py-4
- Full-width button

### Desktop (≥ 768px)

- Card padding: p-10 md:p-12
- Full font sizes: text-5xl for title
- Input/button padding: py-5
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

### Spacing

```
gap-3, gap-6                 /* Component spacing */
p-6, p-10, p-12              /* Card padding */
mt-20                        /* Back link margin */
```

---

## Edge Cases & Brainstorming

### 1. User Submits Same Email Multiple Times

**Behavior:**
- Backend should rate-limit (e.g., max 3 emails per hour)
- Frontend shows cooldown timer: "You can resend in 30s"
- After cooldown, allow resend

---

### 2. User Closes Page After Submission

**Behavior:**
- Email is already sent
- User can return to reset page later with OTP from email
- No special handling needed

---

### 3. User Has Multiple Accounts with Same Email

**Behavior:**
- Backend returns error: "Multiple accounts found. Please contact support."
- Frontend displays error with support link

---

### 4. Email Goes to Spam

**Behavior:**
- User clicks "Didn't receive email?"
- Resend button available after 30s cooldown
- Suggest checking spam folder in success message

---

### 5. User Types Email with Extra Spaces

**Behavior:**
- Frontend trims email before submission
- " user@example.com " → "user@example.com"

---

### 6. Browser Auto-fill Suggests Wrong Email

**Behavior:**
- User can clear and type correct email
- No special handling needed

---

### 7. User Navigates Back After Success

**Behavior:**
- Success state is lost (local state)
- Page shows form again
- Consider storing success flag in sessionStorage (not in v1)

---

### 8. Slow Network Connection

**Behavior:**
- Submit button shows spinner indefinitely
- No timeout (wait for API response)
- User can't retry until response received

**Enhancement (v2):**
- Add timeout after 30 seconds
- Show "Request timed out. Please try again."

---

## Acceptance Criteria

### Functional Requirements

- [ ] User can enter email address
- [ ] Email validation works (format check)
- [ ] Submit button disabled until valid email
- [ ] API call on submit
- [ ] Success message displays
- [ ] Resend button works with cooldown
- [ ] Back to login link works
- [ ] Prefill email from URL param

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
| `frontend/src/pages/auth/ForgotPasswordPage.jsx` | Modify | Full implementation (currently skeleton) |
| `frontend/src/pages/auth/ForgotPasswordPage.stories.jsx` | Create | Storybook stories |

---

## Implementation Notes

### Do's

- ✅ Use `useApiMutation` hook for API calls
- ✅ Use `cn()` for class merging
- ✅ Use Lucide React icons consistently
- ✅ Follow existing LoginPage design patterns
- ✅ Use `toast` from sonner for notifications
- ✅ Use `useSearchParams` for URL params
- ✅ Trim email before submission
- ✅ Validate email format client-side

### Don'ts

- ❌ Don't use raw `fetch()` — use SDK client
- ❌ Don't concatenate class strings — use `cn()`
- ❌ Don't use hardcoded colors — use design tokens
- ❌ Don't reveal if email exists (security consideration)
- ❌ Don't allow rapid resends (implement cooldown)

---

## Security Considerations

### Email Enumeration Prevention

**Current Approach:** Show error if email not found
- **Pro:** Better UX, users know immediately
- **Con:** Allows attackers to check if email is registered

**Alternative Approach:** Always show success
- **Pro:** Prevents email enumeration
- **Con:** Confusing for users with typos

**Decision:** Show error for better UX. Backend should implement rate limiting to prevent abuse.

---

## Rate Limiting Strategy

**Frontend Cooldown:**
- 30 seconds between resends
- Visible countdown timer
- Button disabled during cooldown

**Backend Rate Limiting:**
- Max 3 emails per hour per IP
- Max 10 emails per day per email address
- HTTP 429 response with `Retry-After` header

---

## Success Message Copy

**Primary Message:**
"Check your inbox! We've sent password reset instructions to {email}"

**Secondary Message (smaller text):**
"Didn't receive the email? Check your spam folder or click 'Resend' below."

**Resend Button:**
- During cooldown: "Resend in {cooldown}s"
- After cooldown: "Resend Email"

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
