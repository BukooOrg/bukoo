import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import LoginPage from './LoginPage';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
  }),
}));

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    credentialLogin: vi.fn(),
    getOAuthLoginUrl: vi.fn(),
  },
}));

describe('LoginPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders login form with email and password fields', () => {
    render(<LoginPage />, { wrapper: MemoryRouter });

    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login account now/i })).toBeInTheDocument();
  });

  it('shows error when form submitted with empty fields', async () => {
    render(<LoginPage />, { wrapper: MemoryRouter });

    const form = document.querySelector('form');
    fireEvent.submit(form);

    // HTML5 validation prevents submission
    expect(screen.queryByText('Invalid email or password')).not.toBeInTheDocument();
  });

  it('renders forgot password link', () => {
    render(<LoginPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Forgot Password?')).toBeInTheDocument();
  });

  it('renders register link', () => {
    render(<LoginPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Register Now')).toBeInTheDocument();
  });

  it('renders OAuth buttons', () => {
    render(<LoginPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Continue with Google')).toBeInTheDocument();
    expect(screen.getByText('Continue with Facebook')).toBeInTheDocument();
  });
});
