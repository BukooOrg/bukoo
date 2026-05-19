import { render, screen, waitFor, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { authApi, userApi } from '@/lib/apiClient';

import { AuthProvider, useAuth } from './AuthContext';

vi.mock('@/lib/apiClient', () => ({
  authApi: {
    logout: vi.fn(),
  },
  userApi: {
    getMe: vi.fn(),
  },
  clearToken: vi.fn(),
}));

function TestConsumer() {
  const { user, loading, login, logout } = useAuth();
  return (
    <div>
      <p data-testid='loading'>{loading ? 'true' : 'false'}</p>
      <p data-testid='user'>{user ? JSON.stringify(user) : 'null'}</p>
      <button data-testid='login-btn' onClick={() => login({ id: '1', role: 'user' })}>
        Login
      </button>
      <button data-testid='logout-btn' onClick={logout}>
        Logout
      </button>
    </div>
  );
}

function renderWithContext() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>
  );
}

describe('AuthContext', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('starts with loading=true and user=null', () => {
    userApi.getMe.mockReturnValue(new Promise(() => {}));

    renderWithContext();

    expect(screen.getByTestId('loading').textContent).toBe('true');
    expect(screen.getByTestId('user').textContent).toBe('null');
  });

  it('fetches user on mount and sets loading=false', async () => {
    userApi.getMe.mockResolvedValue({
      data: { id: '1', email: 'test@test.com', role: 'user' },
    });

    renderWithContext();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toContain('test@test.com');
  });

  it('handles fetch error gracefully', async () => {
    userApi.getMe.mockRejectedValue(new Error('Auth check failed'));

    renderWithContext();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
  });

  it('login sets user directly when userData has role', async () => {
    userApi.getMe.mockResolvedValue({ data: null });

    renderWithContext();

    await waitFor(() => {
      expect(screen.getByTestId('loading').textContent).toBe('false');
    });

    const initialCallCount = userApi.getMe.mock.calls.length;

    act(() => {
      screen.getByTestId('login-btn').click();
    });

    expect(screen.getByTestId('user').textContent).toContain('role');
    // getMe should not have been called again (only during mount)
    expect(userApi.getMe.mock.calls.length).toBe(initialCallCount);
  });

  it('logout clears user and calls authApi.logout', async () => {
    userApi.getMe.mockResolvedValue({
      data: { id: '1', role: 'user' },
    });

    renderWithContext();

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toContain('role');
    });

    act(() => {
      screen.getByTestId('logout-btn').click();
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(authApi.logout).toHaveBeenCalled();
  });
});
