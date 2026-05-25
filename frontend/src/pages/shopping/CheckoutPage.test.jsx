import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CheckoutPage from '@/pages/shopping/CheckoutPage';

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

const mockUseCart = vi.fn();

vi.mock('@/components/cart/CartContext', () => ({
  useCart: () => mockUseCart(),
  CartProvider: ({ children }) => children,
}));

const mockBookApi = {
  viewBookDetail: vi.fn(({ bookId }) =>
    Promise.resolve({
      data: {
        id: bookId,
        title: bookId === 'book-1' ? 'The Great Gatsby' : '1984',
        price: bookId === 'book-1' ? '25.00' : '20.00',
        stockQuantity: 10,
      },
    })
  ),
};

const mockUserApi = {
  getMyAddress: vi.fn(() => Promise.resolve({ data: { recipientName: 'Test User' } })),
};

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    placeOrder: vi.fn(),
  },
  userApi: {
    getMyAddress: (...args) => mockUserApi.getMyAddress(...args),
  },
  bookApi: {
    viewBookDetail: (...args) => mockBookApi.viewBookDetail(...args),
  },
  getToken: () => 'mock-token',
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

const mockCartItems = [
  {
    id: 'cart-1',
    bookId: 'book-1',
    quantity: 2,
    book: {
      title: 'The Great Gatsby',
      price: '25.00',
      coverUrl: 'https://example.com/cover.jpg',
    },
  },
  {
    id: 'cart-2',
    bookId: 'book-2',
    quantity: 1,
    book: {
      title: '1984',
      price: '20.00',
      coverUrl: null,
    },
  },
];

function renderWithCart(cartValue) {
  mockUseCart.mockReturnValue(cartValue);

  return render(
    <MemoryRouter>
      <CheckoutPage />
    </MemoryRouter>
  );
}

async function waitForReady() {
  await waitFor(() => {
    expect(screen.queryByRole('status')).not.toBeInTheDocument();
  });
}

describe('CheckoutPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockBookApi.viewBookDetail.mockImplementation(({ bookId }) =>
      Promise.resolve({
        data: {
          id: bookId,
          title: bookId === 'book-1' ? 'The Great Gatsby' : '1984',
          price: bookId === 'book-1' ? '25.00' : '20.00',
          stockQuantity: 10,
        },
      })
    );
    mockUserApi.getMyAddress.mockImplementation(() =>
      Promise.resolve({ data: { recipientName: 'Test User' } })
    );
  });

  it('shows loading spinner when cart is loading', () => {
    renderWithCart({ cart: { items: [] }, loading: true });
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows empty cart message when cart has no items', async () => {
    renderWithCart({ cart: { items: [] }, loading: false });
    await waitForReady();
    expect(screen.getByText('Your Cart is Empty')).toBeInTheDocument();
    expect(screen.getByText('Browse Books')).toBeInTheDocument();
  });

  it('renders checkout heading with items in cart', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('Checkout')).toBeInTheDocument();
    expect(screen.getByText(/Order Items/)).toBeInTheDocument();
  });

  it('renders cart item titles', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
    expect(screen.getByText('1984')).toBeInTheDocument();
  });

  it('renders item quantities', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('Qty: 2')).toBeInTheDocument();
    expect(screen.getByText('Qty: 1')).toBeInTheDocument();
  });

  it('renders item line totals', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('RM 50.00')).toBeInTheDocument();
    expect(screen.getByText('RM 20.00')).toBeInTheDocument();
  });

  it('renders order summary section', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('Order Summary')).toBeInTheDocument();
    expect(screen.getByText('Subtotal')).toBeInTheDocument();
    expect(screen.getByText('Shipping')).toBeInTheDocument();
    expect(screen.getByText('Total')).toBeInTheDocument();
  });

  it('calculates correct subtotal', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('RM 70.00')).toBeInTheDocument();
  });

  it('shows shipping cost', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('RM 5.00')).toBeInTheDocument();
  });

  it('calculates correct total', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('RM 75.00')).toBeInTheDocument();
  });

  it('renders place order button', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('Place Order')).toBeInTheDocument();
  });

  it('places order and navigates to payment on success', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.placeOrder.mockResolvedValueOnce({
      data: { id: 'order-123' },
    });

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(orderApi.placeOrder).toHaveBeenCalledWith({
        placeOrderRequest: { cartItemIds: ['cart-2', 'cart-1'] },
      });
      expect(mockNavigate).toHaveBeenCalledWith('/checkout/payment?orderId=order-123');
    });
  });

  it('shows error toast when place order fails', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.placeOrder.mockRejectedValueOnce(new Error('Failed'));

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Failed to place order');
    });
  });

  it('shows placing order state while request is in progress', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.placeOrder.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 5000))
    );

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));
    expect(screen.getByText('Placing Order...')).toBeInTheDocument();
  });

  it('sorts items alphabetically by title', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    const titles = screen.getAllByText(/^(1984|The Great Gatsby)$/);
    expect(titles[0].textContent).toBe('1984');
    expect(titles[1].textContent).toBe('The Great Gatsby');
  });

  it('shows no cover placeholder when item has no cover image', async () => {
    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();
    expect(screen.getByText('No cover')).toBeInTheDocument();
  });

  it('renders browse books link when cart is empty', async () => {
    renderWithCart({ cart: { items: [] }, loading: false });
    await waitForReady();
    const link = screen.getByText('Browse Books').closest('a');
    expect(link).toHaveAttribute('href', '/shop');
  });

  it('redirects to address page when user has no saved address', async () => {
    const { toast } = await import('sonner');
    mockUserApi.getMyAddress.mockImplementationOnce(() => Promise.resolve({ data: null }));

    renderWithCart({ cart: { items: mockCartItems }, loading: false });

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please add a shipping address before checkout');
      expect(mockNavigate).toHaveBeenCalledWith('/account/address', { replace: true });
    });
  });

  it('shows out of stock error when backend returns OUT_OF_STOCK', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.placeOrder.mockRejectedValueOnce({
      response: { data: { error: { code: 'OUT_OF_STOCK', message: 'Item out of stock' } } },
    });

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Item out of stock');
    });
  });

  it('shows book not found error when backend returns BOOK_NOT_FOUND', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.placeOrder.mockRejectedValueOnce({
      response: { data: { error: { code: 'BOOK_NOT_FOUND' } } },
    });

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('A book in your cart is no longer available');
    });
  });

  it('shows address error when backend returns ADDRESS_NOT_FOUND', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.placeOrder.mockRejectedValueOnce({
      response: { data: { error: { code: 'ADDRESS_NOT_FOUND' } } },
    });

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please add a shipping address before checkout');
    });
  });

  it('prevents placing order when book is out of stock (client-side check)', async () => {
    const { toast } = await import('sonner');
    mockBookApi.viewBookDetail.mockImplementation(({ bookId }) =>
      Promise.resolve({
        data: {
          id: bookId,
          title: bookId === 'book-1' ? 'The Great Gatsby' : '1984',
          price: bookId === 'book-1' ? '25.00' : '20.00',
          stockQuantity: bookId === 'book-2' ? 0 : 10,
        },
      })
    );

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });

  it('prevents placing order when price has changed (client-side check)', async () => {
    const { toast } = await import('sonner');
    mockBookApi.viewBookDetail.mockImplementation(({ bookId }) =>
      Promise.resolve({
        data: {
          id: bookId,
          title: bookId === 'book-1' ? 'The Great Gatsby' : '1984',
          price: bookId === 'book-1' ? '30.00' : '20.00',
          stockQuantity: 10,
        },
      })
    );

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });

  it('prevents placing order when stock is insufficient (client-side check)', async () => {
    const { toast } = await import('sonner');
    mockBookApi.viewBookDetail.mockImplementation(({ bookId }) =>
      Promise.resolve({
        data: {
          id: bookId,
          title: bookId === 'book-1' ? 'The Great Gatsby' : '1984',
          price: bookId === 'book-1' ? '25.00' : '20.00',
          stockQuantity: bookId === 'book-1' ? 1 : 10,
        },
      })
    );

    renderWithCart({ cart: { items: mockCartItems }, loading: false });
    await waitForReady();

    fireEvent.click(screen.getByText('Place Order'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalled();
    });
  });
});
