import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AccountOrdersPage from '@/pages/account/OrdersPage';

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
  },
  {
    id: 'order-456-def',
    status: 'paid',
    total: '75.00',
    item_count: 3,
    created_at: '2024-02-20T14:30:00Z',
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
      <AccountOrdersPage />
    </MemoryRouter>
  );
}

describe('AccountOrdersPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows orders list after loading', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });
  });

  it('shows order IDs', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Order #order-12/)).toBeInTheDocument();
      expect(screen.getByText(/Order #order-45/)).toBeInTheDocument();
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
      expect(screen.getByText('2 items')).toBeInTheDocument();
      expect(screen.getByText('3 items')).toBeInTheDocument();
    });
  });

  it('links to order detail page', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      const link = screen.getByText(/Order #order-12/).closest('a');
      expect(link).toHaveAttribute('href', '/account/orders/order-123-abc');
    });
  });

  it('shows empty state when no orders', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce({
      data: { items: [], meta: { totalPages: 1 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('No Orders Yet')).toBeInTheDocument();
      expect(screen.getByText('Browse Books')).toBeInTheDocument();
    });
  });

  it('filters orders by status', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Orders')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'pending' } });

    await waitFor(() => {
      expect(orderApi.findOrders).toHaveBeenCalledWith(
        expect.objectContaining({ status: 'pending' })
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

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'paid' } });

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
      expect(screen.getByText('Previous')).toBeInTheDocument();
      expect(screen.getByText('Next')).toBeInTheDocument();
    });
  });

  it('disables previous button on first page', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.findOrders.mockResolvedValueOnce({
      data: { items: mockOrders, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Previous')).toBeDisabled();
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
});
