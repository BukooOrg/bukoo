import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AccountOrderDetailPage from '@/pages/account/OrderDetailPage';

const mockNavigate = vi.fn();
const mockOrderId = 'order-123-abc';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useParams: () => ({ orderId: mockOrderId }),
  };
});

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    viewOrderDetail: vi.fn(),
    cancelOrder: vi.fn(),
  },
  bookApi: {
    viewBookDetail: vi.fn().mockResolvedValue({
      data: { coverUrl: 'https://example.com/cover.jpg' },
    }),
  },
}));

vi.mock('@/components/cart/ConfirmDialog', () => ({
  ConfirmDialog: ({ open, onOpenChange, title, description, onConfirm, loading }) => {
    if (!open) return null;
    return (
      <div data-testid='confirm-dialog'>
        <p>{title}</p>
        <p>{description}</p>
        <button onClick={onConfirm} disabled={loading}>
          Confirm
        </button>
      </div>
    );
  },
}));

const mockPendingOrder = {
  id: 'order-123-abc',
  status: 'pending',
  subtotal: '45.00',
  shipping_cost: '5.00',
  total: '50.00',
  created_at: '2024-01-15T10:00:00Z',
  items: [
    {
      id: 'item-1',
      book_title: 'The Great Gatsby',
      quantity: 1,
      line_total: '25.00',
    },
    {
      id: 'item-2',
      book_title: '1984',
      quantity: 1,
      line_total: '20.00',
    },
  ],
  address_snapshot: {
    line1: '123 Main St',
    line2: 'Apt 4B',
    city: 'Kuala Lumpur',
    state: 'KL',
    postalCode: '50000',
  },
  payment: {
    method: 'online_banking',
    status: 'success',
  },
};

const mockPaidOrder = {
  ...mockPendingOrder,
  status: 'paid',
};

const mockShippedOrder = {
  ...mockPendingOrder,
  status: 'shipped',
};

function renderPage() {
  return render(
    <MemoryRouter>
      <AccountOrderDetailPage />
    </MemoryRouter>
  );
}

describe('AccountOrderDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows order details after loading', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Order Details')).toBeInTheDocument();
    });
  });

  it('shows order ID', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Order #order-12/)).toBeInTheDocument();
    });
  });

  it('shows order status badge', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Pending')).toBeInTheDocument();
    });
  });

  it('shows order items', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
      expect(screen.getByText('1984')).toBeInTheDocument();
    });
  });

  it('shows item quantities', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getAllByText('Qty: 1').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows order summary', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Summary')).toBeInTheDocument();
      expect(screen.getByText('RM 45.00')).toBeInTheDocument();
      expect(screen.getByText('RM 5.00')).toBeInTheDocument();
      expect(screen.getByText('RM 50.00')).toBeInTheDocument();
    });
  });

  it('shows shipping address', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

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
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Method: online banking')).toBeInTheDocument();
      expect(screen.getByText('Status: success')).toBeInTheDocument();
    });
  });

  it('shows cancel button for pending orders', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPendingOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Cancel Order')).toBeInTheDocument();
    });
  });

  it('shows cancel button for paid orders', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockPaidOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Cancel Order')).toBeInTheDocument();
    });
  });

  it('hides cancel button for shipped orders', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockShippedOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.queryByText('Cancel Order')).not.toBeInTheDocument();
    });
  });

  it('cancels order on confirm', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValue({ data: mockPendingOrder });
    orderApi.cancelOrder.mockResolvedValueOnce({});

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Cancel Order')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Cancel Order'));

    await waitFor(() => {
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Confirm'));

    await waitFor(() => {
      expect(orderApi.cancelOrder).toHaveBeenCalledWith({ orderId: 'order-123-abc' });
    });
  });

  it('navigates to orders list when order not found', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockRejectedValueOnce(new Error('Not found'));

    renderPage();

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/account/orders');
    });
  });

  it('shows error toast when cancel fails', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.viewOrderDetail.mockResolvedValue({ data: mockPendingOrder });
    orderApi.cancelOrder.mockRejectedValueOnce(new Error('Failed'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Cancel Order')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Cancel Order'));

    await waitFor(() => {
      expect(screen.getByTestId('confirm-dialog')).toBeInTheDocument();
    });

    fireEvent.click(screen.getByText('Confirm'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to cancel order');
    });
  });
});
