import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import VerifyEmailPage from './VerifyEmailPage';

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    verifyEmail: vi.fn(),
    resendEmailVerification: vi.fn(),
  },
}));

describe('VerifyEmailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders OTP input', () => {
    render(<VerifyEmailPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Verification Code')).toBeInTheDocument();
  });

  it('renders 6 digit input boxes', () => {
    render(<VerifyEmailPage />, { wrapper: MemoryRouter });
    const inputs = screen.getAllByRole('textbox');
    expect(inputs).toHaveLength(6);
  });

  it('disables submit button with less than 6 digits', () => {
    render(<VerifyEmailPage />, { wrapper: MemoryRouter });

    const submitButton = screen.getByRole('button', { name: /verify email/i });
    expect(submitButton).toBeDisabled();
  });

  it('renders resend button', () => {
    render(<VerifyEmailPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Resend')).toBeInTheDocument();
  });
});
