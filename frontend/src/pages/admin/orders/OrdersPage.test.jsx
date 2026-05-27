import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AdminOrdersPage from '@/pages/admin/orders/OrdersPage';

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    findOrders: vi.fn(),
    updateOrderStatus: vi.fn(),
  },
  userApi: {
    viewUserProfile: vi.fn().mockResolvedValue({
      data: { fullName: 'Test User', email: 'test@example.com' },
    }),
  },
}));

const mockOrders = [
  {
    id: 'order-123-abc',
    status: 'pending',
    total: '50.00',
    itemCount: 2,
    createdAt: '2024-01-15T10:00:00Z',
    userId: 'user-1',
  },
  {
    id: 'order-456-def',
    status: 'paid',
    total: '75.00',
    itemCount: 3,
    createdAt: '2024-02-20T14:30:00Z',
    userId: 'user-2',
  },
];

const mockPaginatedResponse = {
  data: {
    items: mockOrders,
    meta: { totalPages: 1 },
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <AdminOrdersPage />
    </MemoryRouter>
  );
}

describe('AdminOrdersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows orders heading', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });
  });

  it('shows search input', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Search orders...')).toBeInTheDocument();
    });
  });

  it('shows status filter', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByRole('combobox')[0]).toBeInTheDocument();
    });
  });

  it('shows orders table with data', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('#order-12')).toBeInTheDocument();
      expect(screen.getByText('#order-45')).toBeInTheDocument();
    });
  });

  it('shows customer names', async () => {
    const { userApi, orderApi } = await import('@/lib/apiClient');
    userApi.viewUserProfile.mockResolvedValue({ data: { fullName: 'Test User' } });
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      const names = screen.getAllByText('Test User');
      expect(names.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows order status badges', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      const badges = screen.getAllByText('Pending');
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows order totals', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('RM 50.00')).toBeInTheDocument();
      expect(screen.getByText('RM 75.00')).toBeInTheDocument();
    });
  });

  it('shows item counts', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
      expect(screen.getByText('3')).toBeInTheDocument();
    });
  });

  it('links to admin order detail', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      const link = screen.getByText('#order-12').closest('a');
      expect(link).toHaveAttribute('href', '/admin/orders/order-123-abc');
    });
  });

  it('shows empty state when no orders', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce({
      data: { items: [], meta: { totalPages: 1 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/No orders.*found/)).toBeInTheDocument();
    });
  });

  it('filters by status', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });

    const select = screen.getAllByRole('combobox')[0];
    fireEvent.change(select, { target: { value: 'pending' } });

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'pending' })
      );
    });
  });

  it('filters by search query', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search orders...');
    fireEvent.change(searchInput, { target: { value: 'John' } });

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(expect.objectContaining({ search: 'John' }));
    });
  });

  it('resets to page 1 when filter changes', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search orders...');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));
    });
  });

  it('shows pagination when multiple pages', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce({
      data: { items: mockOrders, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
  });

  it('navigates to next page', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue({
      data: { items: mockOrders, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Next')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
    });
  });

  it('shows N/A for orders without user', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce({
      data: {
        items: [{ ...mockOrders[0], userId: null }],
        meta: { totalPages: 1 },
      },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Deleted')).toBeInTheDocument();
    });
  });
});
