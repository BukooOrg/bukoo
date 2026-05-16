import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import PasswordPage from './PasswordPage';

vi.mock('@/lib/apiClient', () => ({
  usersApi: {
    changePassword: vi.fn(),
  },
}));

vi.mock('@/hooks/useApiMutation', () => ({
  useApiMutation: () => ({
    mutate: vi.fn(),
    loading: false,
  }),
}));

describe('PasswordPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', () => {
    render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('heading', { name: /change password/i })).toBeInTheDocument();
  });

  it('renders current password input', () => {
    const { container } = render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    const inputs = container.querySelectorAll('input[type="password"]');
    expect(inputs[0]).toBeInTheDocument();
  });

  it('renders new password input', () => {
    const { container } = render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    const inputs = container.querySelectorAll('input[type="password"]');
    expect(inputs[1]).toBeInTheDocument();
  });

  it('renders confirm password input', () => {
    const { container } = render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    const inputs = container.querySelectorAll('input[type="password"]');
    expect(inputs[2]).toBeInTheDocument();
  });

  it('shows password strength meter when typing new password', () => {
    const { container } = render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    const inputs = container.querySelectorAll('input[type="password"]');
    const newPasswordInput = inputs[1];
    fireEvent.change(newPasswordInput, { target: { value: 'weak' } });

    expect(screen.getByText('Weak')).toBeInTheDocument();
  });

  it('renders change password button', () => {
    render(
      <MemoryRouter>
        <PasswordPage />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /change password/i })).toBeInTheDocument();
  });
});
