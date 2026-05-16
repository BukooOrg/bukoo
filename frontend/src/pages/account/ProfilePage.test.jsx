import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ProfilePage from './ProfilePage';

vi.mock('@/lib/apiClient', () => ({
  usersApi: {
    getMe: vi.fn(),
    updateProfile: vi.fn(),
    updateAvatar: vi.fn(),
    removeAvatar: vi.fn(),
  },
}));

vi.mock('@/hooks/useApiQuery', () => ({
  useApiQuery: () => ({
    data: {
      fullName: 'Test User',
      email: 'test@test.com',
      dateOfBirth: '1990-01-01',
      avatarUrl: null,
    },
    loading: false,
  }),
}));

vi.mock('@/hooks/useApiMutation', () => ({
  useApiMutation: () => ({
    mutate: vi.fn(),
    loading: false,
  }),
}));

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.getByText('Profile')).toBeInTheDocument();
  });

  it('renders avatar upload section', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.getByText('Profile Photo')).toBeInTheDocument();
  });

  it('renders full name input with current value', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.getByDisplayValue('Test User')).toBeInTheDocument();
  });

  it('renders date of birth input with current value', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument();
  });

  it('renders save button', () => {
    render(
      <MemoryRouter>
        <ProfilePage />
      </MemoryRouter>
    );

    expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
  });
});
