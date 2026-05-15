# Auth API Set - Frontend Testing Strategy

## Overview

| Field | Value |
|-------|-------|
| **API Set** | 1. Auth API Set |
| **Pages** | 6 pages (Register, VerifyEmail, Login, OAuthCallback, ForgotPassword, ResetPassword) |
| **Components** | 4 components (OtpInput, OtpInputBox, PasswordStrengthMeter, OAuthProviderIcon) |
| **Hooks** | 2 hooks (useApiQuery, useApiMutation) |
| **Priority** | High |
| **Status** | Proposal — Ready for review |

---

## Testing Layers

### 1. Unit Tests

**Tool:** Vitest + React Testing Library

**What It Tests:**
- Individual components in isolation
- Custom hooks
- Utility functions
- Form validation schemas

**Coverage Target:** 80%+ for components and hooks

---

### 2. Integration Tests

**Tool:** Vitest + React Testing Library

**What It Tests:**
- Page components with mocked API
- Form submission flows
- State management
- Error handling

**Coverage Target:** 70%+ for pages

---

### 3. E2E Tests

**Tool:** Playwright

**What It Tests:**
- Full user flows across multiple pages
- Real API integration
- Browser navigation
- Responsive design

**Coverage Target:** All critical user flows

---

## Test Files Structure

```
frontend/src/
├── pages/auth/
│   ├── LoginPage.jsx
│   ├── LoginPage.test.jsx          ← Integration tests
│   ├── LoginPage.stories.jsx       ← Storybook stories
│   ├── RegisterPage.jsx
│   ├── RegisterPage.test.jsx       ← Integration tests
│   ├── VerifyEmailPage.jsx
│   ├── VerifyEmailPage.test.jsx    ← Integration tests
│   ├── ForgotPasswordPage.jsx
│   ├── ForgotPasswordPage.test.jsx ← Integration tests
│   ├── ResetPasswordPage.jsx
│   ├── ResetPasswordPage.test.jsx  ← Integration tests
│   ├── OAuthLoginPage.jsx
│   └── OAuthLoginPage.test.jsx     ← Integration tests
├── components/auth/
│   ├── otp-input.jsx
│   ├── otp-input.test.jsx          ← Unit tests
│   ├── otp-input.stories.jsx
│   ├── otp-input-box.jsx
│   ├── otp-input-box.test.jsx      ← Unit tests
│   ├── password-strength-meter.jsx
│   └── password-strength-meter.test.jsx ← Unit tests
├── hooks/
│   ├── useApiQuery.js
│   ├── useApiQuery.test.js         ← Unit tests
│   ├── useApiMutation.js
│   └── useApiMutation.test.js      ← Unit tests
└── __tests__/
    └── e2e/
        ├── auth-flow.spec.js       ← E2E: Register → Verify → Login
        └── password-reset.spec.js  ← E2E: Forgot → Reset → Login
```

---

## Unit Test Scenarios

### OtpInput Component

| Test | Description |
|------|-------------|
| `renders 6 input boxes` | Checks that 6 OtpInputBox components are rendered |
| `auto-advances on digit entry` | Enters digit, checks focus moves to next box |
| `handles backspace` | Presses backspace on empty box, checks focus moves back |
| `handles paste` | Pastes "123456", checks all boxes filled |
| `handles paste with non-digits` | Pastes "12-34-56", checks only digits are used |
| `calls onChange on digit entry` | Enters digit, checks onChange callback called |
| `disables all inputs when disabled` | Sets disabled prop, checks all inputs disabled |
| `shows error state` | Sets error prop, checks error styling applied |

### OtpInputBox Component

| Test | Description |
|------|-------------|
| `renders input element` | Checks that input is rendered |
| `displays value` | Sets value prop, checks input value |
| `calls onChange on input` | Types digit, checks onChange called |
| `calls onKeyDown on key press` | Presses key, checks onKeyDown called |
| `calls onFocus on focus` | Focuses input, checks onFocus called |
| `auto-focuses on mount when first and empty` | Renders first box, checks auto-focus |
| `selects text on focus` | Focuses input, checks text selected |
| `applies error styling` | Sets error prop, checks error class applied |

### PasswordStrengthMeter Component

| Test | Description |
|------|-------------|
| `shows empty state for empty password` | Empty password, checks no strength shown |
| `shows weak for short password` | "weak", checks weak label and red color |
| `shows medium for partial requirements` | "Medium1", checks medium label and yellow color |
| `shows strong for full requirements` | "Str0ng!Pass", checks strong label and green color |
| `updates on password change` | Changes password, checks strength updates |

### useApiQuery Hook

| Test | Description |
|------|-------------|
| `fetches data on mount` | Renders hook, checks data populated |
| `sets loading to true initially` | Renders hook, checks loading is true |
| `sets loading to false after fetch` | Waits for fetch, checks loading is false |
| `handles error` | Mocks error response, checks error state |
| `skips fetch when skip is true` | Sets skip option, checks no fetch |
| `cancels fetch on unmount` | Unmounts during fetch, checks no state update |

### useApiMutation Hook

| Test | Description |
|------|-------------|
| `mutates data on call` | Calls mutate, checks data populated |
| `sets loading to true during mutation` | Calls mutate, checks loading is true |
| `sets loading to false after mutation` | Waits for mutation, checks loading is false |
| `handles error` | Mocks error response, checks error state |
| `calls onSuccess callback` | Mocks success, checks onSuccess called |
| `calls onError callback` | Mocks error, checks onError called |

---

## Integration Test Scenarios

### RegisterPage

| Test | Description |
|------|-------------|
| `renders registration form` | Checks all form fields present |
| `validates email format` | Enters invalid email, checks error message |
| `validates password match` | Enters mismatched passwords, checks error |
| `validates date of birth` | Enters future date, checks error |
| `submits valid form` | Fills form, submits, checks API call |
| `shows loading during submission` | Submits, checks spinner visible |
| `shows error on API failure` | Mocks error response, checks error message |
| `redirects on success` | Mocks success response, checks navigation |

### VerifyEmailPage

| Test | Description |
|------|-------------|
| `renders OTP input` | Checks OTP input component present |
| `auto-verifies with token in URL` | Renders with ?token=123456, checks auto-submit |
| `submits OTP` | Enters 6 digits, submits, checks API call |
| `shows loading during verification` | Submits, checks spinner visible |
| `shows error on invalid OTP` | Mocks error response, checks error message |
| `shows success on valid OTP` | Mocks success response, checks success state |
| `resends verification email` | Clicks resend, checks API call |
| `shows cooldown timer` | Resends, checks countdown visible |

### ForgotPasswordPage

| Test | Description |
|------|-------------|
| `renders email form` | Checks email input present |
| `validates email format` | Enters invalid email, checks error message |
| `submits valid email` | Enters email, submits, checks API call |
| `shows loading during submission` | Submits, checks spinner visible |
| `shows error on user not found` | Mocks error response, checks error message |
| `shows success on valid email` | Mocks success response, checks success state |
| `resends reset email` | Clicks resend, checks API call |
| `shows cooldown timer` | Resends, checks countdown visible |

### ResetPasswordPage

| Test | Description |
|------|-------------|
| `renders password form` | Checks password inputs present |
| `shows password strength meter` | Enters password, checks strength meter visible |
| `validates password strength` | Enters weak password, checks error message |
| `validates password match` | Enters mismatched passwords, checks error |
| `toggles password visibility` | Clicks eye icon, checks password visible |
| `submits valid form` | Fills form, submits, checks API call |
| `shows loading during submission` | Submits, checks spinner visible |
| `shows error on invalid token` | Mocks error response, checks error message |
| `shows success on valid reset` | Mocks success response, checks success state |

---

## E2E Test Scenarios

### Full Registration Flow

```javascript
// e2e/auth-flow.spec.js

test('user can register, verify email, and login', async ({ page }) => {
  // 1. Navigate to registration page
  await page.goto('/register');
  
  // 2. Fill registration form
  await page.fill('[name="full_name"]', 'Test User');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="date_of_birth"]', '1990-01-01');
  await page.fill('[name="password"]', 'Test1234!');
  await page.fill('[name="confirm_password"]', 'Test1234!');
  
  // 3. Submit registration
  await page.click('button[type="submit"]');
  
  // 4. Wait for redirect to verify email
  await page.waitForURL('/verify-email');
  
  // 5. Enter OTP (mocked from email)
  await page.fill('[data-testid="otp-input"]', '123456');
  await page.click('button[type="submit"]');
  
  // 6. Wait for redirect to login
  await page.waitForURL('/login');
  
  // 7. Login with credentials
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'Test1234!');
  await page.click('button[type="submit"]');
  
  // 8. Verify successful login
  await page.waitForURL('/');
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
});
```

### Password Reset Flow

```javascript
// e2e/password-reset.spec.js

test('user can reset password and login with new password', async ({ page }) => {
  // 1. Navigate to forgot password
  await page.goto('/forgot-password');
  
  // 2. Enter email
  await page.fill('[name="email"]', 'test@example.com');
  await page.click('button[type="submit"]');
  
  // 3. Wait for success message
  await expect(page.locator('text=Check your inbox')).toBeVisible();
  
  // 4. Navigate to reset password (simulating email link)
  await page.goto('/reset-password?email=test@example.com&otp=123456');
  
  // 5. Enter new password
  await page.fill('[name="password"]', 'NewPass123!');
  await page.fill('[name="confirm_password"]', 'NewPass123!');
  await page.click('button[type="submit"]');
  
  // 6. Wait for success message
  await expect(page.locator('text=Password reset successful')).toBeVisible();
  
  // 7. Wait for redirect to login
  await page.waitForURL('/login');
  
  // 8. Login with new password
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'NewPass123!');
  await page.click('button[type="submit"]');
  
  // 9. Verify successful login
  await page.waitForURL('/');
  await expect(page.locator('[data-testid="user-menu"]')).toBeVisible();
});
```

---

## Test Setup

### Vitest Configuration

```javascript
// vitest.config.js
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/__tests__/setup.js'],
    globals: true,
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/__tests__/',
        '**/*.stories.jsx',
        '**/*.config.js',
      ],
    },
  },
});
```

### Test Setup File

```javascript
// src/__tests__/setup.js
import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock React Router
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useSearchParams: () => [new URLSearchParams(), vi.fn()],
    useParams: () => ({ provider: 'google' }),
  };
});

// Mock sonner toast
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));
```

### Playwright Configuration

```javascript
// playwright.config.js
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './src/__tests__/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
  ],
  webServer: {
    command: 'pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
  },
});
```

---

## Test Commands

### Package.json Scripts

```json
{
  "scripts": {
    "test": "vitest",
    "test:unit": "vitest run src/components src/hooks",
    "test:integration": "vitest run src/pages",
    "test:coverage": "vitest run --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:all": "pnpm test:coverage && pnpm test:e2e"
  }
}
```

---

## Mock API Responses

### Auth API Mocks

```javascript
// src/__tests__/mocks/authApi.js

export const mockRegisterResponse = {
  success: true,
  data: {
    id: 'user-123',
    email: 'test@example.com',
    fullName: 'Test User',
    status: 'pending',
    role: 'user',
  },
  meta: {
    requestId: 'req-123',
    timestamp: '2024-01-01T00:00:00Z',
  },
};

export const mockVerifyEmailResponse = {
  success: true,
  data: {
    id: 'user-123',
    email: 'test@example.com',
    status: 'active',
  },
  meta: {
    requestId: 'req-124',
    timestamp: '2024-01-01T00:00:00Z',
  },
};

export const mockForgotPasswordResponse = {
  success: true,
  data: {
    message: 'Reset email sent',
  },
  meta: {
    requestId: 'req-125',
    timestamp: '2024-01-01T00:00:00Z',
  },
};

export const mockResetPasswordResponse = {
  success: true,
  data: {
    message: 'Password reset successful',
  },
  meta: {
    requestId: 'req-126',
    timestamp: '2024-01-01T00:00:00Z',
  },
};

export const mockErrorResponse = {
  success: false,
  error: {
    code: 'INVALID_OTP',
    message: 'Invalid verification code',
    details: null,
  },
  meta: {
    requestId: 'req-127',
    timestamp: '2024-01-01T00:00:00Z',
  },
};
```

---

## Coverage Targets

| Category | Target | Current |
|----------|--------|---------|
| **Components** | 80%+ | 0% (not started) |
| **Hooks** | 90%+ | 0% (not started) |
| **Pages** | 70%+ | 0% (not started) |
| **E2E Flows** | 100% | 0% (not started) |

---

## Definition of Done

- [ ] Proposal reviewed and approved
- [ ] Test setup configured (Vitest, Playwright)
- [ ] Unit tests for all components
- [ ] Unit tests for all hooks
- [ ] Integration tests for all pages
- [ ] E2E tests for critical flows
- [ ] Coverage targets met
- [ ] All tests passing
- [ ] CI/CD pipeline updated

---

**Next Steps:**
1. Review this proposal
2. Approve or request changes
3. Set up test infrastructure
4. Write tests following this specification
5. Run tests and verify coverage
