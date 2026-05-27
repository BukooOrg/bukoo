import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AdminOrderDetailPage from '@/pages/admin/orders/OrderDetailPage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ orderId: 'order-123-abc' }),
  };
});

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    viewOrderDetail: vi.fn(),
    updateOrderStatus: vi.fn(),
  },
  bookApi: {
    viewBookDetail: vi.fn().mockResolvedValue({
      data: { coverUrl: 'https://example.com/cover.jpg' },
    }),
  },
}));

const mockOrder = {
  id: 'order-123-abc',
  status: 'pending',
  subtotal: '45.00',
  shippingCost: '5.00',
  total: '50.00',
  createdAt: '2024-01-15T10:00:00Z',
  items: [
    {
      id: 'item-1',
      bookTitle: 'The Great Gatsby',
      bookCoverUrl: 'https://example.com/cover1.jpg',
      unitPrice: '25.00',
      quantity: 1,
      lineTotal: '25.00',
    },
    {
      id: 'item-2',
      bookTitle: '1984',
      bookCoverUrl: 'https://example.com/cover2.jpg',
      unitPrice: '20.00',
      quantity: 1,
      lineTotal: '20.00',
    },
  ],
  user: {
    name: 'John Doe',
    email: 'john@example.com',
  },
  addressSnapshot: {
    address_line1: '123 Main St',
    address_line2: 'Apt 4B',
    city: 'Kuala Lumpur',
    state: 'KL',
    postcode: '50000',
  },
  payment: {
    method: 'online_banking',
    status: 'success',
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <AdminOrderDetailPage />
    </MemoryRouter>
  );
}

describe('AdminOrderDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows order details after loading', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Order #order-12/)).toBeInTheDocument();
    });
  });

  it('shows order status badge', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      const badges = screen.getAllByText('Pending');
      expect(badges.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows order items', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
      expect(screen.getByText('1984')).toBeInTheDocument();
    });
  });

  it('shows item quantities', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText('Qty: 1').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows order summary', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Summary')).toBeInTheDocument();
      expect(screen.getByText('RM 45.00')).toBeInTheDocument();
      expect(screen.getByText('RM 5.00')).toBeInTheDocument();
      expect(screen.getByText('RM 50.00')).toBeInTheDocument();
    });
  });

  it('shows customer info', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Customer')).toBeInTheDocument();
      expect(screen.getByText('John Doe')).toBeInTheDocument();
      expect(screen.getByText('john@example.com')).toBeInTheDocument();
    });
  });

  it('shows shipping address', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Shipping Address')).toBeInTheDocument();
      const addressSection = screen.getByText('Shipping Address').parentElement;
      expect(addressSection?.textContent).toContain('123 Main St');
      expect(addressSection?.textContent).toContain('Kuala Lumpur');
    });
  });

  it('shows payment info', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Method: online banking')).toBeInTheDocument();
      expect(screen.getByText('Status: success')).toBeInTheDocument();
    });
  });

  it('shows order not found when API fails', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockRejectedValueOnce(new Error('Not found'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Order Not Found')).toBeInTheDocument();
      expect(screen.getByText('Back to Orders')).toBeInTheDocument();
    });
  });
});
