import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CheckoutConfirmationPage from '@/pages/shopping/CheckoutConfirmationPage';

const mockSearchParams = new URLSearchParams('orderId=test-order-123');

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useSearchParams: () => [mockSearchParams, vi.fn()],
  };
});

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    viewOrderDetail: vi.fn(),
  },
  bookApi: {
    viewBookDetail: vi.fn().mockResolvedValue({
      data: { coverUrl: 'https://example.com/cover.jpg' },
    }),
  },
}));

vi.mock('@/components/cart/CartContext', () => ({
  useCart: () => ({
    refreshCart: vi.fn().mockResolvedValue(undefined),
  }),
  CartProvider: ({ children }) => children,
}));

const mockOrder = {
  id: 'test-order-123',
  status: 'paid',
  subtotal: '45.00',
  shippingCost: '5.00',
  total: '50.00',
  createdAt: '2024-01-15T10:00:00Z',
  items: [
    {
      id: 'item-1',
      bookTitle: 'The Great Gatsby',
      unitPrice: '25.00',
      quantity: 1,
      lineTotal: '25.00',
    },
    {
      id: 'item-2',
      bookTitle: '1984',
      unitPrice: '20.00',
      quantity: 1,
      lineTotal: '20.00',
    },
  ],
};

function renderPage() {
  return render(
    <MemoryRouter>
      <CheckoutConfirmationPage />
    </MemoryRouter>
  );
}

describe('CheckoutConfirmationPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.set('orderId', 'test-order-123');
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows order confirmed message on success', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Order Confirmed')).toBeInTheDocument();
    });
  });

  it('shows order ID', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/Order #test-ord/)).toBeInTheDocument();
    });
  });

  it('shows order status badge', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Paid')).toBeInTheDocument();
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
      const qtyElements = screen.getAllByText(/Qty: 1/);
      expect(qtyElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows item line totals', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('RM 25.00')).toBeInTheDocument();
      expect(screen.getByText('RM 20.00')).toBeInTheDocument();
    });
  });

  it('shows order summary totals', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('RM 45.00')).toBeInTheDocument();
      expect(screen.getByText('RM 5.00')).toBeInTheDocument();
      expect(screen.getByText('RM 50.00')).toBeInTheDocument();
    });
  });

  it('shows view order button', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('View Order')).toBeInTheDocument();
    });
  });

  it('shows continue shopping button', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockResolvedValueOnce({ data: mockOrder });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Continue Shopping')).toBeInTheDocument();
    });
  });

  it('shows order not found when API fails', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.viewOrderDetail.mockRejectedValueOnce(new Error('Not found'));

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Order Not Found')).toBeInTheDocument();
      expect(screen.getByText('Continue Shopping')).toBeInTheDocument();
    });
  });

  it('shows order not found when orderId is missing', () => {
    mockSearchParams.delete('orderId');
    renderPage();
    expect(screen.getByText('Order Not Found')).toBeInTheDocument();
  });
});
