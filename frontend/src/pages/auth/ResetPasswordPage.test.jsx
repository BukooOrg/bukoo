import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ResetPasswordPage from './ResetPasswordPage';

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    resetPassword: vi.fn(),
  },
}));

describe('ResetPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders new password and confirm password fields', () => {
    render(
      <MemoryRouter initialEntries={['/reset-password?email=test@test.com&otp=123456']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByPlaceholderText('Enter new password')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Re-enter new password')).toBeInTheDocument();
  });

  it('shows password strength meter', () => {
    render(
      <MemoryRouter initialEntries={['/reset-password?email=test@test.com&otp=123456']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByPlaceholderText('Enter new password');
    fireEvent.change(passwordInput, { target: { value: 'weak' } });

    expect(screen.getByText('Weak')).toBeInTheDocument();
  });

  it('shows error when passwords do not match', () => {
    render(
      <MemoryRouter initialEntries={['/reset-password?email=test@test.com&otp=123456']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );

    const passwordInput = screen.getByPlaceholderText('Enter new password');
    const confirmInput = screen.getByPlaceholderText('Re-enter new password');

    fireEvent.change(passwordInput, { target: { value: 'Password1!' } });
    fireEvent.change(confirmInput, { target: { value: 'Password2!' } });

    const form = document.querySelector('form');
    fireEvent.submit(form);

    expect(screen.getByText('Passwords do not match')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(
      <MemoryRouter initialEntries={['/reset-password?email=test@test.com&otp=123456']}>
        <ResetPasswordPage />
      </MemoryRouter>
    );
    expect(screen.getByRole('button', { name: /reset password/i })).toBeInTheDocument();
  });
});
