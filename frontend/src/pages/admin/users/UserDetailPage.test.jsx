import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import UserDetailPage from '@/pages/admin/users/UserDetailPage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ userId: 'user-1' }),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/lib/apiClient', () => ({
  userApi: {
    viewUserProfile: vi.fn(),
    suspendUser: vi.fn(),
    activateUser: vi.fn(),
    softDeleteUser: vi.fn(),
    forceSetUserPassword: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockUser = {
  id: 'user-1',
  fullName: 'Alice Admin',
  email: 'alice@bukoo.com',
  role: 'admin',
  status: 'active',
  dateOfBirth: '1990-05-15',
  havePassword: true,
  lastLoginAt: '2024-06-15T10:00:00Z',
  createdAt: '2024-01-10T08:00:00Z',
  updatedAt: '2024-06-15T10:00:00Z',
};

const mockRegularUser = {
  ...mockUser,
  fullName: 'Bob Reader',
  email: 'bob@bukoo.com',
  role: 'user',
};

const mockSuspendedUser = {
  ...mockUser,
  status: 'suspended',
  role: 'user',
};

function renderWithRouter(ui) {
  return render(
    <MemoryRouter>
      <Routes>
        <Route path='*' element={ui} />
      </Routes>
    </MemoryRouter>
  );
}

describe('UserDetailPage', () => {
  let userApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    userApi = mod.userApi;
    userApi.viewUserProfile.mockResolvedValue({ data: mockUser });
    userApi.suspendUser.mockResolvedValue({ data: {} });
    userApi.activateUser.mockResolvedValue({ data: {} });
    userApi.softDeleteUser.mockResolvedValue({ data: {} });
    userApi.forceSetUserPassword.mockResolvedValue({ data: {} });
  });

  it('renders loading skeleton initially', () => {
    renderWithRouter(<UserDetailPage />);

    const skeleton = document.querySelector('.animate-pulse');
    expect(skeleton).toBeTruthy();
  });

  it('renders user profile data after loading', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    });

    expect(screen.getByText('alice@bukoo.com')).toBeInTheDocument();
    expect(screen.getByText('admin')).toBeInTheDocument();
    expect(screen.getByText('Yes')).toBeInTheDocument();
  });

  it('renders role badge', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      const roleBadges = screen.getAllByText('Admin');
      expect(roleBadges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders status badge', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('renders account info section', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Account Info')).toBeInTheDocument();
    });

    expect(screen.getByText('Email')).toBeInTheDocument();
    expect(screen.getByText('Role')).toBeInTheDocument();
    expect(screen.getByText('Date of Birth')).toBeInTheDocument();
    expect(screen.getByText('Has Password')).toBeInTheDocument();
  });

  it('renders activity section', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Activity')).toBeInTheDocument();
    });

    expect(screen.getByText('Last Login')).toBeInTheDocument();
    expect(screen.getByText('Created')).toBeInTheDocument();
    expect(screen.getByText('Last Updated')).toBeInTheDocument();
  });

  it('renders actions section for regular users', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockRegularUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Actions')).toBeInTheDocument();
    });

    expect(screen.getByText('Reset Password')).toBeInTheDocument();
    expect(screen.getByText('Delete User')).toBeInTheDocument();
  });

  it('hides actions section for active admin users', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.queryByText('Actions')).not.toBeInTheDocument();
    });
  });

  it('shows actions section for suspended admin users (activate only)', async () => {
    userApi.viewUserProfile.mockResolvedValue({
      data: { ...mockUser, status: 'suspended' },
    });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Actions')).toBeInTheDocument();
      expect(screen.getByText('Activate User')).toBeInTheDocument();
    });
  });

  it('shows suspend button for non-admin active users', async () => {
    userApi.viewUserProfile.mockResolvedValue({
      data: { ...mockUser, status: 'active', role: 'user' },
    });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Suspend User')).toBeInTheDocument();
    });
  });

  it('hides suspend button for admin users', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.queryByText('Suspend User')).not.toBeInTheDocument();
    });
  });

  it('shows activate button for suspended users', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockSuspendedUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Activate User')).toBeInTheDocument();
    });
  });

  it('hides activate button for active users', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.queryByText('Activate User')).not.toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    userApi.viewUserProfile.mockRejectedValueOnce(new Error('Not found'));

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Failed to load user profile')).toBeInTheDocument();
    });
  });

  it('suspends user when confirmed', async () => {
    userApi.viewUserProfile.mockResolvedValue({
      data: { ...mockUser, status: 'active', role: 'user' },
    });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Suspend User')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Suspend User'));
    });

    await waitFor(() => {
      expect(screen.getByText('Suspend User?')).toBeInTheDocument();
    });

    const dialog = screen.getByRole('alertdialog');
    const confirmButton = dialog.querySelector('button[class*="bg-destructive"]');

    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(userApi.suspendUser).toHaveBeenCalledWith({ userId: 'user-1' });
    });
  });

  it('activates user when confirmed', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockSuspendedUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Activate User')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Activate User'));
    });

    await waitFor(() => {
      expect(screen.getByText('Activate User?')).toBeInTheDocument();
    });

    const dialog = screen.getByRole('alertdialog');
    const confirmButton = dialog.querySelector('button:last-child');

    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(userApi.activateUser).toHaveBeenCalledWith({ userId: 'user-1' });
    });
  });

  it('deletes user when confirmed', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockRegularUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Delete User')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Delete User'));
    });

    await waitFor(() => {
      expect(screen.getByText('Delete User?')).toBeInTheDocument();
    });

    const dialog = screen.getByRole('alertdialog');
    const confirmButton = dialog.querySelector('button[class*="bg-destructive"]');

    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(userApi.softDeleteUser).toHaveBeenCalledWith({ userId: 'user-1' });
    });
  });

  it('opens password reset dialog', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockRegularUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Reset Password'));
    });

    await waitFor(() => {
      expect(screen.getByText('Force Password Reset')).toBeInTheDocument();
    });
  });

  it('submits password reset with new password', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockRegularUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Reset Password'));
    });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter new password')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.change(screen.getByPlaceholderText('Enter new password'), {
        target: { value: 'NewSecure123!' },
      });
    });

    const dialog = screen.getByRole('dialog');
    const buttons = dialog.querySelectorAll('button');
    const resetButton = Array.from(buttons).find((btn) =>
      btn.textContent.includes('Reset Password')
    );

    await act(async () => {
      fireEvent.click(resetButton);
    });

    await waitFor(() => {
      expect(userApi.forceSetUserPassword).toHaveBeenCalledWith({
        userId: 'user-1',
        forceSetUserPasswordRequest: { newPassword: 'NewSecure123!' },
      });
    });
  });

  it('toggles password visibility', async () => {
    userApi.viewUserProfile.mockResolvedValue({ data: mockRegularUser });

    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Reset Password')).toBeInTheDocument();
    });

    await act(async () => {
      fireEvent.click(screen.getByText('Reset Password'));
    });

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter new password')).toBeInTheDocument();
    });

    const passwordInput = screen.getByPlaceholderText('Enter new password');
    expect(passwordInput).toHaveAttribute('type', 'password');

    const toggleButtons = screen.getAllByRole('button');
    const eyeButton = toggleButtons.find(
      (btn) => btn.querySelector('svg') && btn.closest('[role="dialog"]')
    );

    if (eyeButton) {
      await act(async () => {
        fireEvent.click(eyeButton);
      });
      expect(passwordInput).toHaveAttribute('type', 'text');
    }
  });

  it('navigates back to users list', async () => {
    renderWithRouter(<UserDetailPage />);

    await waitFor(() => {
      expect(screen.getByText('Back to Users')).toBeInTheDocument();
    });

    const backLink = screen.getByText('Back to Users').closest('a');
    expect(backLink).toHaveAttribute('href', '/admin/users');
  });
});
