# Verify Email Page Proposal

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **API Endpoint** | `POST /api/app/v1/auth/verify-email` (API 1.2) |
| **Route** | `/verify-email` |
| **Access Level** | 🌐 Public |
| **Priority** | High |
| **Status** | Proposal — Ready for review |

---

## User Flow

```
User Registration → Email sent with OTP → User clicks verification link
                                           ↓
                                    VerifyEmailPage
                                           ↓
                              [Option A: Token in URL]
                              Auto-verify if token present
                                           ↓
                              [Option B: Manual OTP entry]
                              User enters 6-digit OTP
                                           ↓
                              Submit → API validates OTP
                                           ↓
                              Success → Redirect to login
                              Error → Show error, allow retry
```

---

## UI Wireframe Description

### Layout Structure

- **Container**: Full-screen centered layout (matches LoginPage style)
- **Card**: White/80 backdrop blur, rounded-40px, shadow-2xl
- **Background**: Abstract blur gradients (top-left, bottom-right)
- **Content**: Vertically centered with proper spacing

### Visual Elements

1. **Icon Section** (top center)
   - Circular icon container (bg-primary/5)
   - Lucide icon: `Mail` or `CheckCircle` (w-7 h-7, text-primary)

2. **Title Section**
   - H1: "Verify Your Email" (font-serif, text-5xl, font-black, text-primary)
   - Subtitle: "Enter the 6-digit code sent to your email" (text-sm, italic, text-primary/40)

3. **OTP Input Component**
   - 6 individual boxes (equal width, ~48px each)
   - Auto-focus on first box
   - Auto-advance to next box on digit input
   - Backspace moves to previous box
   - Paste support for 6-digit code
   - Visual states: default, focused, filled, error

4. **Submit Button**
   - Full-width, py-5, bg-primary, text-secondary
   - Loading state: spinner icon
   - Disabled during submission

5. **Resend Link Section**
   - "Didn't receive code?" text
   - "Resend" button (inline, text-primary, hover:underline)
   - Cooldown timer: 30 seconds between resends

6. **Back Link**
   - "Back to Home" (text-xs, uppercase, tracking-widest)
   - Positioned below card with mt-20

---

## Component Tree

```
VerifyEmailPage (default export)
├── AuthLayout (route wrapper from App.jsx)
├── VerifyEmailCard
│   ├── IconSection
│   │   └── Mail icon (lucide-react)
│   ├── TitleSection
│   │   ├── H1 title
│   │   └── Subtitle paragraph
│   ├── OtpInput
│   │   └── OtpInputBox × 6 (internal component)
│   ├── SubmitButton
│   │   ├── Loader2 (loading state)
│   │   └── CheckCircle (success state)
│   ├── ResendSection
│   │   ├── Static text
│   │   ├── ResendButton
│   │   └── CooldownTimer
│   └── BackToHome (Link component)
└── Toaster (from sonner)
```

---

## State Requirements

### Local State (useState)

| State | Type | Initial | Purpose |
|-------|------|---------|---------|
| `otp` | string | `''` | Current OTP value (6 digits) |
| `isSubmitting` | boolean | `false` | Submission in progress |
| `error` | string | `''` | Error message to display |
| `success` | boolean | `false` | Verification successful |
| `cooldown` | number | `0` | Seconds until resend available |
| `email` | string | `null` | User's email (from registration flow) |

### URL Query Parameters

| Param | Type | Required | Purpose |
|-------|------|----------|---------|
| `token` | string | No | Pre-filled verification token (optional) |
| `email` | string | No | Pre-fill email for resend |

### Context Dependencies

- **None** — This is a public page, no auth required
- Uses `useNavigate` from react-router-dom
- Uses `useSearchParams` for token/email extraction

---

## Form Schema (Zod)

```javascript
import { z } from 'zod';

export const verifyEmailSchema = z.object({
  otp: z
    .string()
    .length(6, 'OTP must be exactly 6 digits')
    .regex(/^\d{6}$/, 'OTP must contain only numbers'),
});

export type VerifyEmailFormData = z.infer<typeof verifyEmailSchema>;
```

---

## New Components Needed

### 1. OtpInput Component

**File:** `src/components/auth/otp-input.jsx`

**Props:**
```jsx
{
  value: string,
  onChange: (value: string) => void,
  onError: (error: string) => void,
  disabled: boolean,
  error: boolean,
}
```

**Features:**
- Renders 6 OtpInputBox components
- Manages focus between boxes
- Handles keyboard navigation (ArrowLeft, ArrowRight, Backspace)
- Handles paste event (validates 6-digit format)
- Auto-submit when 6th digit is entered (optional)

**Internal State:**
- `focusedIndex` — Which box has focus (0-5)

---

### 2. OtpInputBox Component

**File:** `src/components/auth/otp-input-box.jsx`

**Props:**
```jsx
{
  index: number,
  value: string,
  onChange: (index: number, value: string) => void,
  onFocus: (index: number) => void,
  onKeyDown: (index: number, e: KeyboardEvent) => void,
  onPaste: (e: ClipboardEvent) => void,
  disabled: boolean,
  error: boolean,
  inputRef: React.RefObject<HTMLInputElement>,
}
```

**Visual States:**
- **Default**: border-primary/20, bg-white/40
- **Focused**: ring-2 ring-primary/10, border-primary
- **Filled**: text-primary, font-bold
- **Error**: border-destructive, ring-destructive/10
- **Disabled**: opacity-50, cursor-not-allowed

---

## API Integration

### SDK Method Call

```javascript
import { authApi } from '@/lib/apiClient';
import { useApiMutation } from '@/hooks/useApiMutation';

const { mutate: verifyEmail, loading, error } = useApiMutation(
  (variables) => authApi.verifyEmail(variables),
  {
    onSuccess: (data) => {
      toast.success('Email verified successfully!');
      setSuccess(true);
      setTimeout(() => navigate('/login'), 2000);
    },
    onError: (err) => {
      const message = err.response?.data?.error?.message || 'Verification failed';
      setError(message);
    },
  }
);

// Usage:
verifyEmail({ verifyEmailRequest: { otp } });
```

### Resend Verification API

```javascript
const { mutate: resendVerification, loading: isResending } = useApiMutation(
  (variables) => authApi.resendEmailVerification(variables),
  {
    onSuccess: () => {
      toast.success('Verification email resent!');
      setCooldown(30);
    },
  }
);

// Usage:
resendVerification({ resendVerificationRequest: { email } });
```

---

## Loading States

### Initial Page Load

- Check for `?token=` query parameter
- If token present: auto-submit immediately
- Show full-page spinner during auto-verification

### During OTP Entry

- No loading state (instant feedback)
- Each digit appears immediately

### During Submission

- Submit button shows spinner (Loader2 icon)
- OTP input becomes disabled
- Button text: "Verifying..."

### Success State

- Show success message with CheckCircle icon
- Green accent color
- Auto-redirect to `/login` after 2 seconds
- Manual "Go to Login" link (in case auto-redirect fails)

---

## Error States

### Invalid OTP (API 422)

**Error Code:** `INVALID_OTP`

**UI Response:**
- Field-level error below OTP input
- Clear OTP after 3 failed attempts
- Show "Too many failed attempts. Please request a new code."

**Message:** "Invalid verification code. Please try again."

---

### Expired Token (API 400)

**Error Code:** `OTP_EXPIRED`

**UI Response:**
- Full error message
- Highlight "Resend" button
- Pre-fill email if available

**Message:** "This verification code has expired. Please request a new one."

---

### Already Verified (API 400)

**Error Code:** `EMAIL_ALREADY_VERIFIED`

**UI Response:**
- Success-style message (not an error)
- Redirect to login after 3 seconds

**Message:** "Email already verified. Redirecting to login..."

---

### Network Error

**UI Response:**
- Generic error message
- Retry button
- No OTP clear

**Message:** "Could not connect to server. Please check your connection and try again."

---

## Storybook Stories

### OtpInput.stories.jsx

```javascript
import { OtpInput } from './otp-input';

export default {
  title: 'Auth/OtpInput',
  component: OtpInput,
  tags: ['autodocs'],
  argTypes: {
    value: { control: 'text' },
    onChange: { action: 'changed' },
    disabled: { control: 'boolean' },
    error: { control: 'boolean' },
  },
};

export const Default = {
  args: {
    value: '',
    disabled: false,
    error: false,
  },
};

export const Filled = {
  args: {
    value: '123456',
    disabled: false,
    error: false,
  },
};

export const PartiallyFilled = {
  args: {
    value: '123',
    disabled: false,
    error: false,
  },
};

export const Error = {
  args: {
    value: '123456',
    disabled: false,
    error: true,
  },
};

export const Disabled = {
  args: {
    value: '123456',
    disabled: true,
    error: false,
  },
};
```

---

### OtpInputBox.stories.jsx

```javascript
import { OtpInputBox } from './otp-input-box';

export default {
  title: 'Auth/OtpInputBox',
  component: OtpInputBox,
  tags: ['autodocs'],
  argTypes: {
    value: { control: 'text' },
    focused: { control: 'boolean' },
    disabled: { control: 'boolean' },
    error: { control: 'boolean' },
  },
};

export const Empty = {
  args: {
    value: '',
    focused: false,
    disabled: false,
    error: false,
  },
};

export const Filled = {
  args: {
    value: '5',
    focused: false,
    disabled: false,
    error: false,
  },
};

export const Focused = {
  args: {
    value: '',
    focused: true,
    disabled: false,
    error: false,
  },
};

export const Error = {
  args: {
    value: 'X',
    focused: false,
    disabled: false,
    error: true,
  },
};
```

---

## Accessibility (A11y) Considerations

### Keyboard Navigation

- **Tab**: Move between OTP boxes
- **ArrowLeft/ArrowRight**: Navigate between boxes
- **Backspace**: Delete current digit, move to previous box
- **Enter**: Submit form (when all 6 digits entered)

### Screen Reader Support

- Each OTP box has `aria-label="Digit 1 of 6"`, etc.
- Error messages use `role="alert"`
- Success message announces "Email verified successfully"
- Loading state: `aria-busy="true"` on submit button

### Focus Management

- Auto-focus first box on page load
- Restore focus after error
- Move focus to success message on completion

---

## Responsive Design

### Mobile (< 768px)

- OTP boxes: 48px width each
- Reduced card padding: p-6
- Smaller font sizes: text-4xl for title
- Full-width button with reduced padding: py-4

### Desktop (≥ 768px)

- OTP boxes: 56px width each
- Standard card padding: p-10 md:p-12
- Full font sizes: text-5xl for title
- Standard button padding: py-5

---

## Design Tokens Used

### Colors

```css
--primary: 31 85% 13%        /* Main brand color */
--secondary: 0 0% 96%        /* Button text */
--destructive: 0 84% 60%     /* Error states */
--background: 0 0% 96%       /* Page background */
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

### 1. User Refreshes Page During Verification

**Behavior:**
- OTP state is lost (local state)
- User must re-enter OTP
- Token in URL is preserved (if present)

**Mitigation:**
- Consider storing OTP in sessionStorage (not implemented in v1)

---

### 2. User Opens Multiple Tabs

**Behavior:**
- Each tab has independent OTP state
- First successful verification invalidates OTP
- Other tabs show "Already verified" on submit

---

### 3. OTP Expires During Entry

**Behavior:**
- User enters 6th digit after expiry
- API returns `OTP_EXPIRED`
- Show error, prompt to resend

---

### 4. Slow Network Connection

**Behavior:**
- Submit button shows spinner
- No timeout (wait for API response)
- User can't retry until response received

**Enhancement (v2):**
- Add timeout after 30 seconds
- Show "Request timed out. Please try again."

---

### 5. Browser Back Button After Success

**Behavior:**
- Redirect happens after 2 seconds
- If user navigates back, page shows success state
- Consider storing verification status in sessionStorage

---

### 6. Copy-Paste OTP with Spaces

**Behavior:**
- Paste handler strips non-digit characters
- "123 456" → "123456"
- "12-34-56" → "123456"

---

### 7. Resend Spam

**Behavior:**
- 30-second cooldown timer
- Button disabled during cooldown
- Timer visible to user: "Resend in 25s"

---

## Acceptance Criteria

### Functional Requirements

- [ ] User can enter 6-digit OTP
- [ ] Auto-advance between boxes works
- [ ] Backspace deletes and moves back
- [ ] Paste 6-digit code works
- [ ] Submit button disabled until 6 digits
- [ ] API call on submit
- [ ] Success redirects to login
- [ ] Error shows appropriate message
- [ ] Resend button works with cooldown

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
| `frontend/src/pages/auth/VerifyEmailPage.jsx` | Modify | Full implementation |
| `frontend/src/components/auth/otp-input.jsx` | Create | OTP input component |
| `frontend/src/components/auth/otp-input-box.jsx` | Create | Individual digit box |
| `frontend/src/components/auth/otp-input.stories.jsx` | Create | Storybook stories |
| `frontend/src/components/auth/otp-input-box.stories.jsx` | Create | Box stories |
| `frontend/src/components/auth/index.js` | Create | Export auth components |

---

## Implementation Notes

### Do's

- ✅ Use `useApiMutation` hook for API calls
- ✅ Use `cn()` for class merging
- ✅ Use Lucide React icons consistently
- ✅ Follow existing LoginPage design patterns
- ✅ Use `toast` from sonner for notifications
- ✅ Use `useSearchParams` for URL params

### Don'ts

- ❌ Don't use raw `fetch()` — use SDK client
- ❌ Don't concatenate class strings — use `cn()`
- ❌ Don't use hardcoded colors — use design tokens
- ❌ Don't store OTP in plain text (beyond local state)
- ❌ Don't auto-submit without user action (unless token in URL)

---

## Definition of Done

- [ ] Proposal reviewed and approved
- [ ] All components implemented
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
