import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ForgotPasswordPage from './ForgotPasswordPage';

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    forgotPassword: vi.fn(),
  },
}));

describe('ForgotPasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders email input field', () => {
    render(<ForgotPasswordPage />, { wrapper: MemoryRouter });
    expect(screen.getByPlaceholderText('Enter your email address')).toBeInTheDocument();
  });

  it('renders submit button', () => {
    render(<ForgotPasswordPage />, { wrapper: MemoryRouter });
    expect(screen.getByRole('button', { name: /send reset instructions/i })).toBeInTheDocument();
  });

  it('shows error for invalid email format', async () => {
    render(<ForgotPasswordPage />, { wrapper: MemoryRouter });

    const emailInput = screen.getByPlaceholderText('Enter your email address');
    fireEvent.change(emailInput, { target: { value: 'invalid-email' } });

    const form = document.querySelector('form');
    fireEvent.submit(form);

    await expect(screen.findByText('Please enter a valid email address')).resolves.toBeInTheDocument();
  });

  it('renders back to login link', () => {
    render(<ForgotPasswordPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
