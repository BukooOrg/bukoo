# Reset Password Page Proposal

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **API Endpoint** | `POST /api/app/v1/auth/password/reset` (API 1.9) |
| **Route** | `/reset-password?email=<email>` |
| **Access Level** | 🌐 Public |
| **Priority** | High |
| **Status** | Proposal — Ready for review |

---

## User Flow

```
User verifies reset link (API 1.8)
                ↓
   /reset-password?email=<email>
                ↓
   Enter new password + confirm
                ↓
   Password strength meter shows strength
                ↓
   Submit → API validates and resets
                ↓
   Success → Redirect to /login
   Error → Show error, allow retry
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
   - Lucide icon: `Lock` or `Shield` (w-7 h-7, text-primary)

2. **Title Section**
   - H1: "Reset Password" (font-serif, text-5xl, font-black, text-primary)
   - Subtitle: "Create a new strong password for your account" (text-sm, italic, text-primary/40)

3. **Password Input Field**
   - Full-width input with icon (Lock icon on left)
   - Label: "New Password" (uppercase, tracking-widest, text-xs)
   - Placeholder: "Enter new password"
   - Show/hide password toggle (Eye icon)
   - Real-time validation feedback

4. **Password Strength Meter** (new component)
   - 3 levels: Weak (red), Medium (yellow), Strong (green)
   - Color-coded bar below password input
   - Text label: "Weak", "Medium", or "Strong"
   - Updates in real-time as user types

5. **Confirm Password Input Field**
   - Full-width input with icon (Lock icon on left)
   - Label: "Confirm Password" (uppercase, tracking-widest, text-xs)
   - Placeholder: "Re-enter new password"
   - Show/hide password toggle (Eye icon)
   - Match indicator (✓/✗)

6. **Submit Button**
   - Full-width, py-5, bg-primary, text-secondary
   - Loading state: spinner icon
   - Disabled until passwords match and meet requirements
   - Icon: `CheckCircle` or `Save`

7. **Success State** (after submission)
   - CheckCircle icon (green)
   - Success message: "Password reset successful!"
   - "Go to Login" button
   - Auto-redirect after 3 seconds

---

## Component Tree

```
ResetPasswordPage (default export)
├── AuthLayout (route wrapper from App.jsx)
├── ResetPasswordCard
│   ├── IconSection
│   │   └── Lock icon (lucide-react)
│   ├── TitleSection
│   │   ├── H1 title
│   │   └── Subtitle paragraph
│   ├── PasswordForm
│   │   ├── NewPasswordInput
│   │   │   ├── Label
│   │   │   ├── Input (with Lock icon)
│   │   │   ├── ShowHideToggle (Eye icon)
│   │   │   └── PasswordStrengthMeter (new component)
│   │   ├── ConfirmPasswordInput
│   │   │   ├── Label
│   │   │   ├── Input (with Lock icon)
│   │   │   ├── ShowHideToggle (Eye icon)
│   │   │   └── MatchIndicator
│   │   ├── SubmitButton
│   │   │   ├── Loader2 (loading state)
│   │   │   └── CheckCircle icon
│   │   └── ErrorMessage (if any)
│   ├── SuccessState (conditional)
│   │   ├── CheckCircle icon
│   │   ├── Success message
│   │   └── GoToLoginButton
│   └── BackToHome (Link component)
└── Toaster (from sonner)
```

---

## State Requirements

### Local State (useState)

| State | Type | Initial | Purpose |
|-------|------|---------|---------|
| `password` | string | `''` | New password value |
| `confirmPassword` | string | `''` | Confirm password value |
| `showPassword` | boolean | `false` | Toggle password visibility |
| `showConfirmPassword` | boolean | `false` | Toggle confirm password visibility |
| `isSubmitting` | boolean | `false` | Submission in progress |
| `error` | string | `''` | Error message to display |
| `success` | boolean | `false` | Password reset successful |
| `email` | string | `''` | Email from URL param |

### URL Query Parameters

| Param | Type | Required | Purpose |
|-------|------|----------|---------|
| `email` | string | Yes | User's email address |
| `otp` | string | Yes | Reset verification token |

---

## Form Schema (Zod)

```javascript
import { z } from 'zod';

export const resetPasswordSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain at least one special character'),
  confirmPassword: z.string().min(1, 'Please confirm your password'),
}).refine((data) => {
  if (data.password !== data.confirmPassword) {
    return {
      message: 'Passwords do not match',
      path: ['confirmPassword'],
    };
  }
  return true;
});

export type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;
```

---

## New Components Needed

### PasswordStrengthMeter Component

**File:** `src/components/auth/password-strength-meter.jsx`

**Props:**
```jsx
{
  password: string,
}
```

**Strength Levels:**

| Level | Conditions | Color | Label |
|-------|------------|-------|-------|
| **Weak** | < 8 chars OR missing 3+ requirements | Red (`--destructive`) | "Weak" |
| **Medium** | 8+ chars AND meets 2-3 requirements | Yellow (`--warning`) | "Medium" |
| **Strong** | 8+ chars AND meets all 4 requirements | Green (`--success`) | "Strong" |

**Requirements Checked:**
1. At least 8 characters
2. Contains uppercase letter
3. Contains lowercase letter
4. Contains number
5. Contains special character

**Visual Design:**
- Progress bar (3 segments)
- Color changes based on strength
- Text label below bar
- Smooth transition animation

---

## API Integration

### SDK Method Call

```javascript
import { authApi } from '@/lib/apiClient';
import { useApiMutation } from '@/hooks/useApiMutation';

const { mutate: resetPassword, loading: isSubmitting, error: apiError } = useApiMutation(
  (variables) => authApi.resetPassword(variables),
  {
    onSuccess: () => {
      setSuccess(true);
      toast.success('Password reset successful!');
      setTimeout(() => navigate('/login'), 3000);
    },
    onError: (err) => {
      const message = err.response?.data?.error?.message || 'Failed to reset password';
      setError(message);
    },
  }
);

// Usage:
resetPassword({ resetPasswordRequest: { email, otp, newPassword: password } });
```

---

## Loading States

### Initial State

- Password inputs enabled
- Submit button disabled (until valid)
- No loading indicators

### During Submission

- Submit button shows spinner (Loader2 icon)
- Button text: "Resetting..."
- Password inputs disabled
- No other loading indicators

### Success State

- Form hidden
- CheckCircle icon appears (green, animated)
- Success message displayed
- "Go to Login" button visible
- Auto-redirect after 3 seconds

---

## Error States

### Password Too Short (Client-side)

**Trigger:** Password < 8 characters

**UI Response:**
- Field-level error below password input
- Input border turns red (border-destructive)
- Error message: "Password must be at least 8 characters"
- Strength meter shows "Weak" (red)

---

### Password Doesn't Meet Requirements (Client-side)

**Trigger:** Missing uppercase, lowercase, number, or special char

**UI Response:**
- Field-level error below password input
- Strength meter shows appropriate level
- Specific error message for missing requirement

---

### Passwords Don't Match (Client-side)

**Trigger:** password !== confirmPassword

**UI Response:**
- Field-level error below confirm password input
- Input border turns red
- Error message: "Passwords do not match"
- Match indicator shows ✗ (red)

---

### Invalid/Expired Token (API 400)

**Error Code:** `INVALID_OTP` or `OTP_EXPIRED`

**UI Response:**
- Full error message below submit button
- Error style: border-destructive/10 bg-destructive/5
- Message: "This reset link is invalid or has expired"
- "Request New Reset Link" button

---

### User Not Found (API 404)

**Error Code:** `USER_NOT_FOUND`

**UI Response:**
- Full error message
- Message: "No account found with this email address"
- "Back to Login" link

---

### Network Error

**UI Response:**
- Generic error message
- Message: "Could not connect to server. Please check your connection and try again."
- Retry button

---

## Storybook Stories

### ResetPasswordPage.stories.jsx

```javascript
import ResetPasswordPage from './ResetPasswordPage';

export default {
  title: 'Auth/ResetPasswordPage',
  component: ResetPasswordPage,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const Default = {
  args: {
    email: 'user@example.com',
    otp: '123456',
  },
};

export const WithWeakPassword = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    password: 'weak',
  },
};

export const WithStrongPassword = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    password: 'Str0ng!Pass',
  },
};

export const PasswordsMismatch = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    password: 'Str0ng!Pass',
    confirmPassword: 'Different!Pass123',
  },
};

export const Submitting = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    isSubmitting: true,
    password: 'Str0ng!Pass',
    confirmPassword: 'Str0ng!Pass',
  },
};

export const Success = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    success: true,
  },
};

export const Error = {
  args: {
    email: 'user@example.com',
    otp: '123456',
    error: 'This reset link is invalid or has expired',
  },
};
```

### PasswordStrengthMeter.stories.jsx

```javascript
import { PasswordStrengthMeter } from './password-strength-meter';

export default {
  title: 'Auth/PasswordStrengthMeter',
  component: PasswordStrengthMeter,
  tags: ['autodocs'],
};

export const Weak = {
  args: {
    password: 'weak',
  },
};

export const Medium = {
  args: {
    password: 'Medium1',
  },
};

export const Strong = {
  args: {
    password: 'Str0ng!Pass',
  },
};

export const Empty = {
  args: {
    password: '',
  },
};
```

---

## Accessibility (A11y) Considerations

### Keyboard Navigation

- **Tab**: Move between password inputs and submit button
- **Enter**: Submit form
- **Escape**: Navigate back to login

### Screen Reader Support

- Password inputs have `aria-label="New password"` and `aria-label="Confirm password"`
- Error messages use `role="alert"`
- Success message announces "Password reset successful"
- Loading state: `aria-busy="true"` on submit button
- Strength meter: `aria-live="polite"` with strength level

### Focus Management

- Auto-focus new password input on page load
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
--warning: 45 93% 47%        /* Medium strength (yellow) */
```

### Typography

```
font-serif: EB Garamond      /* Headings */
font-sans: Inter             /* Body text, inputs */
```

---

## Edge Cases & Brainstorming

### 1. User Pastes Password from Password Manager

**Behavior:**
- Strength meter updates immediately
- If strong, submit button enables
- No special handling needed

---

### 2. User Types Password with Caps Lock On

**Behavior:**
- Show warning: "Caps Lock is on"
- Non-blocking warning (user can still submit)
- Detect via `getModifierState('CapsLock')` on keydown

---

### 3. User Navigates Back After Success

**Behavior:**
- Success state is lost (local state)
- Page shows form again
- Consider storing success flag in sessionStorage (not in v1)

---

### 4. Slow Network Connection

**Behavior:**
- Submit button shows spinner indefinitely
- No timeout (wait for API response)
- User can't retry until response received

**Enhancement (v2):**
- Add timeout after 30 seconds
- Show "Request timed out. Please try again."

---

### 5. User Edits URL Parameters Manually

**Behavior:**
- Invalid email/otp format
- API returns 400
- Show error state
- No special handling needed

---

## Acceptance Criteria

### Functional Requirements

- [ ] User can enter new password
- [ ] User can confirm password
- [ ] Password strength meter works
- [ ] Show/hide password toggle works
- [ ] Submit button disabled until valid
- [ ] API call on submit
- [ ] Success message displays
- [ ] Auto-redirect to login
- [ ] Prefill email from URL param

### Visual Requirements

- [ ] Matches LoginPage design style
- [ ] Responsive on mobile and desktop
- [ ] Loading states visible
- [ ] Error states clearly indicated
- [ ] Success state with animation
- [ ] Strength meter color-coded

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
| `frontend/src/pages/auth/ResetPasswordPage.jsx` | Modify | Full implementation (currently skeleton) |
| `frontend/src/components/auth/password-strength-meter.jsx` | Create | Password strength meter component |
| `frontend/src/pages/auth/ResetPasswordPage.stories.jsx` | Create | Storybook stories |
| `frontend/src/components/auth/password-strength-meter.stories.jsx` | Create | Strength meter stories |

---

## Implementation Notes

### Do's

- ✅ Use `useApiMutation` hook for API calls
- ✅ Use `cn()` for class merging
- ✅ Use Lucide React icons consistently
- ✅ Follow existing LoginPage design patterns
- ✅ Use `toast` from sonner for notifications
- ✅ Use `useSearchParams` for URL params
- ✅ Validate password strength client-side
- ✅ Show/hide password toggle

### Don'ts

- ❌ Don't use raw `fetch()` — use SDK client
- ❌ Don't concatenate class strings — use `cn()`
- ❌ Don't use hardcoded colors — use design tokens
- ❌ Don't allow weak passwords
- ❌ Don't submit if passwords don't match

---

## Definition of Done

- [ ] Proposal reviewed and approved
- [ ] Page component implemented
- [ ] PasswordStrengthMeter component created
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
