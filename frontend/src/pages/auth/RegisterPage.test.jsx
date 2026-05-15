import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import RegisterPage from './RegisterPage';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    login: vi.fn(),
  }),
}));

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    register: vi.fn(),
  },
}));

describe('RegisterPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders registration form with all fields', () => {
    render(<RegisterPage />, { wrapper: MemoryRouter });

    expect(screen.getByPlaceholderText('Enter your name')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your email')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Min. 8 characters')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Re-enter password')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create account/i })).toBeInTheDocument();
  });

  it('shows password strength meter when password is entered', () => {
    render(<RegisterPage />, { wrapper: MemoryRouter });

    const passwordInput = screen.getByPlaceholderText('Min. 8 characters');
    fireEvent.change(passwordInput, { target: { value: 'weak' } });

    expect(screen.getByText('Weak')).toBeInTheDocument();
  });

  it('shows error when passwords do not match', async () => {
    render(<RegisterPage />, { wrapper: MemoryRouter });

    const form = document.querySelector('form');
    const passwordInput = screen.getByPlaceholderText('Min. 8 characters');
    const confirmInput = screen.getByPlaceholderText('Re-enter password');

    fireEvent.change(passwordInput, { target: { value: 'password1' } });
    fireEvent.change(confirmInput, { target: { value: 'password2' } });
    fireEvent.submit(form);

    await expect(screen.findByText('Passwords do not match')).resolves.toBeInTheDocument();
  });

  it('renders login link', () => {
    render(<RegisterPage />, { wrapper: MemoryRouter });
    expect(screen.getByText('Login')).toBeInTheDocument();
  });
});
