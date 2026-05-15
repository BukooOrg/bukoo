# OAuth Login Page Proposal

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **API Endpoint** | `GET /api/app/v1/auth/oauth/{provider}/login` (API 1.5a) |
| **Route** | `/oauth/{provider}/login` (e.g., `/oauth/google/login`) |
| **Access Level** | 🌐 Public |
| **Priority** | Low |
| **Status** | Proposal — Ready for review |

---

## User Flow

```
User clicks "Continue with Google" on LoginPage
                ↓
   Navigate to /oauth/google/login
                ↓
   Page shows loading spinner
                ↓
   API call: GET /auth/oauth/google/login
                ↓
   ┌─────────────┴─────────────┐
   │                           │
   ▼                           ▼
Success (URL returned)      Error
   │                           │
   ▼                           ▼
window.location.href =      Show error message
response.data.url           "Could not start sign-in"
   │                           │
   ▼                           ▼
Redirect to OAuth provider  "Try again" button
                            "Back to Login" link
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
   - Provider-specific icon (Google/Facebook logo)
   - Size: w-14 h-14

2. **Title Section**
   - H1: "Connecting to {Provider}" (font-serif, text-5xl, font-black, text-primary)
   - Subtitle: "Please wait while we redirect you..." (text-sm, italic, text-primary/40)

3. **Loading State**
   - Large spinner (Loader2, w-12 h-12, text-primary)
   - Centered in card
   - No other content visible

4. **Error State**
   - AlertCircle icon (destructive, w-16 h-16)
   - Message: "Could not start sign-in. Please try again."
   - "Try Again" button
   - "Back to Login" link

---

## Component Tree

```
OAuthLoginPage (default export)
├── AuthLayout (route wrapper from App.jsx)
├── OAuthLoginCard
│   ├── IconSection
│   │   └── Provider icon (Google/Facebook)
│   ├── TitleSection
│   │   ├── H1 title
│   │   └── Subtitle paragraph
│   ├── LoadingState (conditional)
│   │   └── Large spinner
│   └── ErrorState (conditional)
│       ├── AlertCircle icon
│       ├── Error message
│       ├── TryAgainButton
│       └── BackToLogin link
└── Toaster (from sonner)
```

---

## State Requirements

### Local State (useState)

| State | Type | Initial | Purpose |
|-------|------|---------|---------|
| `status` | 'loading' \| 'error' | 'loading' | Current OAuth login status |
| `error` | string | `''` | Error message to display |
| `provider` | string | `''` | OAuth provider from URL |

### URL Path Parameters

| Param | Type | Required | Purpose |
|-------|------|----------|---------|
| `provider` | string | Yes | OAuth provider (google, facebook) |

---

## API Integration

### SDK Method Call

```javascript
import { authApi } from '@/lib/apiClient';
import { useApiQuery } from '@/hooks/useApiQuery';

const { data, loading, error } = useApiQuery(
  () => authApi.getOAuthLoginUrl({ provider }),
  {
    skip: !provider,
  }
);

// On success: redirect to OAuth provider URL
useEffect(() => {
  if (data?.url) {
    window.location.href = data.url;
  }
}, [data]);
```

---

## Loading States

### Initial Load

- Check for `provider` in URL path
- If missing: show error immediately
- If present: call API to get OAuth URL
- Show large spinner during API call

### During API Call

- Spinner centered
- No other interactive elements
- Background dimmed slightly

---

## Error States

### Missing Provider Parameter

**Trigger:** No provider in URL path

**UI Response:**
- Error state immediately
- Message: "Invalid sign-in link. Please try again."
- "Back to Login" link

---

### API Error (Network/Server)

**Error Code:** Various

**UI Response:**
- Error state
- Message: "Could not start sign-in. Please try again."
- "Try Again" button
- "Back to Login" link

---

### Unsupported Provider

**Error Code:** `INVALID_PROVIDER`

**UI Response:**
- Error state
- Message: "This sign-in method is not available."
- "Back to Login" link

---

## Storybook Stories

### OAuthLoginPage.stories.jsx

```javascript
import OAuthLoginPage from './OAuthLoginPage';

export default {
  title: 'Auth/OAuthLoginPage',
  component: OAuthLoginPage,
  tags: ['autodocs'],
  parameters: {
    layout: 'fullscreen',
  },
};

export const GoogleLoading = {
  args: {
    provider: 'google',
    status: 'loading',
  },
};

export const FacebookLoading = {
  args: {
    provider: 'facebook',
    status: 'loading',
  },
};

export const Error = {
  args: {
    provider: 'google',
    status: 'error',
    error: 'Could not start sign-in. Please try again.',
  },
};

export const MissingProvider = {
  args: {
    provider: '',
    status: 'error',
    error: 'Invalid sign-in link. Please try again.',
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

- Loading state: `aria-live="polite"` with "Connecting to {provider}"
- Error state: `role="alert"` with error message
- All buttons have descriptive labels

### Focus Management

- Auto-focus "Try Again" button on error
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
- Icon sizes: w-14 h-14
- Standard button width

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

---

## Edge Cases & Brainstorming

### 1. User Opens Link Directly (Not from LoginPage)

**Behavior:**
- Valid provider in URL
- API call happens normally
- Redirect to OAuth provider
- No special handling needed

---

### 2. User Edits URL to Invalid Provider

**Behavior:**
- API returns 400
- Show error state
- "Back to Login" link

---

### 3. User Navigates Back After Redirect

**Behavior:**
- OAuth flow already started
- Page shows loading again
- API call happens again
- Consider storing redirect status in sessionStorage (not in v1)

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

- [ ] Auto-redirect to OAuth provider on success
- [ ] Show loading state during API call
- [ ] Show error state on failure
- [ ] "Try Again" button works
- [ ] "Back to Login" link works
- [ ] Handle missing provider parameter

### Visual Requirements

- [ ] Matches LoginPage design style
- [ ] Responsive on mobile and desktop
- [ ] Loading states visible
- [ ] Error states clearly indicated

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
| `frontend/src/pages/auth/OAuthLoginPage.jsx` | Create | OAuth login redirect page |
| `frontend/src/pages/auth/OAuthLoginPage.stories.jsx` | Create | Storybook stories |

---

## Implementation Notes

### Do's

- ✅ Use `useApiQuery` hook for API call
- ✅ Use `cn()` for class merging
- ✅ Use Lucide React icons consistently
- ✅ Follow existing LoginPage design patterns
- ✅ Use `toast` from sonner for notifications
- ✅ Use `useParams` for provider from URL
- ✅ Auto-redirect on success

### Don'ts

- ❌ Don't use raw `fetch()` — use SDK client
- ❌ Don't concatenate class strings — use `cn()`
- ❌ Don't use hardcoded colors — use design tokens
- ❌ Don't show form (this is redirect only)
- ❌ Don't allow retry without error state

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
