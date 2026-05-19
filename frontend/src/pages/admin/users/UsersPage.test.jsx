import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import UsersPage from '@/pages/admin/users/UsersPage';

vi.mock('@/lib/apiClient', () => ({
  userApi: {
    findUsers: vi.fn(),
    suspendUser: vi.fn(),
    activateUser: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockUsers = [
  {
    id: 'user-1',
    fullName: 'Alice Admin',
    email: 'alice@bukoo.com',
    role: 'admin',
    status: 'active',
    lastLoginAt: '2024-06-15T10:00:00Z',
    createdAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'user-2',
    fullName: 'Bob User',
    email: 'bob@bukoo.com',
    role: 'user',
    status: 'active',
    lastLoginAt: '2024-05-20T14:30:00Z',
    createdAt: '2024-02-15T09:00:00Z',
  },
  {
    id: 'user-3',
    fullName: 'Charlie Suspended',
    email: 'charlie@bukoo.com',
    role: 'user',
    status: 'suspended',
    lastLoginAt: '2024-03-01T12:00:00Z',
    createdAt: '2024-03-01T12:00:00Z',
  },
  {
    id: 'user-4',
    fullName: 'Diana Pending',
    email: 'diana@bukoo.com',
    role: 'user',
    status: 'pending',
    lastLoginAt: null,
    createdAt: '2024-04-01T12:00:00Z',
  },
];

function mockApiResponse(items, totalItems) {
  return {
    data: {
      items,
      pagination: {
        page: 1,
        pageSize: 20,
        totalItems,
        totalPages: Math.ceil(totalItems / 20) || 1,
        hasNext: false,
        hasPrev: false,
      },
    },
  };
}

describe('UsersPage', () => {
  let userApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    userApi = mod.userApi;
    userApi.findUsers.mockResolvedValue(mockApiResponse(mockUsers, mockUsers.length));
    userApi.suspendUser.mockResolvedValue({ data: {} });
    userApi.activateUser.mockResolvedValue({ data: {} });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Users')).toBeInTheDocument();
    });
  });

  it('renders total user count', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('4 users total')).toBeInTheDocument();
    });
  });

  it('renders new admin button', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Admin')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search users/i)).toBeInTheDocument();
    });
  });

  it('renders all user names in table', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
      expect(screen.getByText('Bob User')).toBeInTheDocument();
      expect(screen.getByText('Charlie Suspended')).toBeInTheDocument();
      expect(screen.getByText('Diana Pending')).toBeInTheDocument();
    });
  });

  it('renders user emails', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('alice@bukoo.com')).toBeInTheDocument();
      expect(screen.getByText('bob@bukoo.com')).toBeInTheDocument();
    });
  });

  it('renders role badges', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Admin')).toBeInTheDocument();
    });
  });

  it('renders status badges', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Suspended')).toBeInTheDocument();
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  it('shows empty state when no users', async () => {
    userApi.findUsers.mockResolvedValueOnce(mockApiResponse([], 0));

    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No users found')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    userApi.findUsers.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load users')).toBeInTheDocument();
    });
  });

  it('filters by role when role button clicked', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    });

    const allRolesButtons = screen.getAllByText('All Roles');
    const roleFilterSection = allRolesButtons[0].closest('div');
    const userRoleButton = roleFilterSection.querySelector('button:nth-child(3)');

    await act(async () => {
      fireEvent.click(userRoleButton);
    });

    await waitFor(() => {
      const calls = userApi.findUsers.mock.calls;
      const lastCall = calls[calls.length - 1][0];
      expect(lastCall.role).toBe('user');
    });
  });

  it('filters by status when status button clicked', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    });

    const allStatusButtons = screen.getAllByText('All Status');
    const statusFilterSection = allStatusButtons[0].closest('div');
    const suspendedButton = statusFilterSection.querySelector('button:nth-child(4)');

    await act(async () => {
      fireEvent.click(suspendedButton);
    });

    await waitFor(() => {
      const calls = userApi.findUsers.mock.calls;
      const lastCall = calls[calls.length - 1][0];
      expect(lastCall.status).toBe('suspended');
    });
  });

  it('searches users when typing in search input', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search users/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search users/i);

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'alice' } });
    });

    await waitFor(
      () => {
        const calls = userApi.findUsers.mock.calls;
        const lastCall = calls[calls.length - 1][0];
        expect(lastCall.search).toBe('alice');
      },
      { timeout: 2000 }
    );
  });

  it('suspends a non-admin active user', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Bob User')).toBeInTheDocument();
    });

    const bobRow = screen.getByText('Bob User').closest('tr');
    const allButtons = bobRow.querySelectorAll('button');
    const powerButton = Array.from(allButtons).find((btn) => {
      const isViewLink = btn.closest('a');
      return !isViewLink;
    });

    expect(powerButton).toBeTruthy();

    await act(async () => {
      fireEvent.click(powerButton);
    });

    await waitFor(() => {
      expect(userApi.suspendUser).toHaveBeenCalledWith({ userId: 'user-2' });
    });
  });

  it('activates a suspended user', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Charlie Suspended')).toBeInTheDocument();
    });

    const charlieRow = screen.getByText('Charlie Suspended').closest('tr');
    const allButtons = charlieRow.querySelectorAll('button');
    const powerButton = Array.from(allButtons).find((btn) => {
      const isViewLink = btn.closest('a');
      return !isViewLink;
    });

    expect(powerButton).toBeTruthy();

    await act(async () => {
      fireEvent.click(powerButton);
    });

    await waitFor(() => {
      expect(userApi.activateUser).toHaveBeenCalledWith({ userId: 'user-3' });
    });
  });

  it('does not show power button for admin users', async () => {
    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    });

    const aliceRow = screen.getByText('Alice Admin').closest('tr');
    const allButtons = aliceRow.querySelectorAll('button');
    const powerButtons = Array.from(allButtons).filter((btn) => {
      const isViewLink = btn.closest('a');
      return !isViewLink;
    });

    expect(powerButtons.length).toBe(0);
  });

  it('renders view button for each user', async () => {
    const { container } = render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const viewLinks = container.querySelectorAll('a[href^="/admin/users/"]');
      expect(viewLinks.length).toBeGreaterThanOrEqual(mockUsers.length);
    });
  });

  it('renders pagination when total pages > 1', async () => {
    userApi.findUsers.mockResolvedValue({
      data: {
        items: mockUsers.slice(0, 2),
        pagination: {
          page: 1,
          pageSize: 2,
          totalItems: 4,
          totalPages: 2,
          hasNext: true,
          hasPrev: false,
        },
      },
    });

    render(
      <MemoryRouter>
        <UsersPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
    });

    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
