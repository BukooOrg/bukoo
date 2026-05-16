import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AccountPage from './AccountPage';

vi.mock('@/lib/apiClient', () => ({
  usersApi: {
    getMe: vi.fn(),
  },
}));

vi.mock('@/hooks/useApiQuery', () => ({
  useApiQuery: () => ({
    data: {
      fullName: 'Test User',
      email: 'test@test.com',
      status: 'active',
      avatarUrl: null,
      createdAt: '2024-01-01T00:00:00Z',
    },
    loading: false,
  }),
}));

describe('AccountPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', () => {
    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('My Account')).toBeInTheDocument();
  });

  it('renders profile summary with user info', () => {
    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@test.com')).toBeInTheDocument();
    expect(screen.getByText('Active')).toBeInTheDocument();
  });

  it('renders quick links', () => {
    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Password')).toBeInTheDocument();
    expect(screen.getByText('Address')).toBeInTheDocument();
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Reviews')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
  });

  it('renders delete account danger zone', () => {
    render(
      <MemoryRouter>
        <AccountPage />
      </MemoryRouter>
    );

    expect(screen.getByText('Delete Account')).toBeInTheDocument();
    expect(screen.getByText('Go to Delete')).toBeInTheDocument();
  });
});
