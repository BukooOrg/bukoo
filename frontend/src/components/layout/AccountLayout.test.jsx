import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { AccountLayout } from './AccountLayout';

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({
    user: {
      fullName: 'Test User',
      email: 'test@test.com',
      avatarUrl: null,
    },
  }),
}));

describe('AccountLayout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders sidebar with navigation links', () => {
    render(
      <MemoryRouter initialEntries={['/account']}>
        <AccountLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('Address')).toBeInTheDocument();
    expect(screen.getByText('Orders')).toBeInTheDocument();
    expect(screen.getByText('Reviews')).toBeInTheDocument();
    expect(screen.getByText('Notifications')).toBeInTheDocument();
    expect(screen.getByText('Password')).toBeInTheDocument();
  });

  it('shows user info in sidebar', () => {
    render(
      <MemoryRouter initialEntries={['/account']}>
        <AccountLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('Test User')).toBeInTheDocument();
    expect(screen.getByText('test@test.com')).toBeInTheDocument();
  });

  it('highlights active nav item', () => {
    render(
      <MemoryRouter initialEntries={['/account/profile']}>
        <AccountLayout />
      </MemoryRouter>
    );

    const profileLink = screen.getByText('Profile').closest('a');
    expect(profileLink).toHaveClass('bg-primary/10');
  });

  it('renders Back to Store link', () => {
    render(
      <MemoryRouter initialEntries={['/account']}>
        <AccountLayout />
      </MemoryRouter>
    );

    expect(screen.getByText('← Back to Store')).toBeInTheDocument();
  });
});
