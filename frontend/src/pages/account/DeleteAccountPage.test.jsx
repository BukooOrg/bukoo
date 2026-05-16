import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import DeleteAccountPage from './DeleteAccountPage';

vi.mock('@/lib/apiClient', () => ({
  usersApi: {
    softDeleteMe: vi.fn(),
  },
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    logout: vi.fn(),
  }),
}));

vi.mock('@/hooks/useApiMutation', () => ({
  useApiMutation: () => ({
    mutate: vi.fn(),
    loading: false,
  }),
}));

describe('DeleteAccountPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', () => {
    render(
      <MemoryRouter>
        <DeleteAccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Delete Account')).toBeInTheDocument();
  });

  it('renders warning card with consequences', () => {
    render(
      <MemoryRouter>
        <DeleteAccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Warning')).toBeInTheDocument();
    expect(
      screen.getByText(/All your personal data will be permanently deleted/)
    ).toBeInTheDocument();
    expect(screen.getByText(/Your order history will be lost/)).toBeInTheDocument();
    expect(screen.getByText(/This action cannot be reversed/)).toBeInTheDocument();
  });

  it('renders confirmation input', () => {
    render(
      <MemoryRouter>
        <DeleteAccountPage />
      </MemoryRouter>
    );

    expect(screen.getByPlaceholderText('DELETE')).toBeInTheDocument();
  });

  it('disables delete button until DELETE is typed', () => {
    render(
      <MemoryRouter>
        <DeleteAccountPage />
      </MemoryRouter>
    );

    const deleteButton = screen.getByRole('button', { name: /permanently delete account/i });
    expect(deleteButton).toBeDisabled();

    const input = screen.getByPlaceholderText('DELETE');
    fireEvent.change(input, { target: { value: 'DELETE' } });

    expect(deleteButton).not.toBeDisabled();
  });
});
