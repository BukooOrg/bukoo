import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AdminOrdersPage from '@/pages/admin/orders/OrdersPage';

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    findOrders: vi.fn(),
  },
}));

const mockOrders = [
  {
    id: 'order-123-abc',
    status: 'pending',
    total: '50.00',
    item_count: 2,
    created_at: '2024-01-15T10:00:00Z',
    user: { name: 'John Doe' },
  },
  {
    id: 'order-456-def',
    status: 'paid',
    total: '75.00',
    item_count: 3,
    created_at: '2024-02-20T14:30:00Z',
    user: { name: 'Jane Smith' },
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

  it('shows user ID filter', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByPlaceholderText('User ID...')).toBeInTheDocument();
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
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('Jane Smith')).toBeInTheDocument();
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
      expect(screen.getByText('No orders found.')).toBeInTheDocument();
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

  it('filters by user ID', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });

    const userIdInput = screen.getByPlaceholderText('User ID...');
    fireEvent.change(userIdInput, { target: { value: 'user-123' } });

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(
        expect.objectContaining({ userId: 'user-123' })
      );
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
        items: [{ ...mockOrders[0], user: null }],
        meta: { totalPages: 1 },
      },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('N/A')).toBeInTheDocument();
    });
  });
});
