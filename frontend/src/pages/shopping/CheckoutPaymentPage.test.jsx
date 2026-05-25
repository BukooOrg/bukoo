import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CheckoutPaymentPage from '@/pages/shopping/CheckoutPaymentPage';

const mockNavigate = vi.fn();
const mockSearchParams = new URLSearchParams('orderId=test-order-123');

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
    useSearchParams: () => [mockSearchParams, vi.fn()],
  };
});

vi.mock('@/lib/apiClient', () => ({
  orderApi: {
    payOrder: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}));

function renderPage() {
  return render(
    <MemoryRouter>
      <CheckoutPaymentPage />
    </MemoryRouter>
  );
}

describe('CheckoutPaymentPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockSearchParams.set('orderId', 'test-order-123');
  });

  it('renders payment heading', () => {
    renderPage();
    expect(screen.getByText('Payment')).toBeInTheDocument();
  });

  it('shows online banking option by default', () => {
    renderPage();
    expect(screen.getByText('Online Banking')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. Maybank')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('e.g. 1234567890')).toBeInTheDocument();
  });

  it('shows credit card option', () => {
    renderPage();
    expect(screen.getByText('Credit / Debit Card')).toBeInTheDocument();
  });

  it('shows card fields when card payment is selected', () => {
    renderPage();
    fireEvent.click(screen.getByText('Credit / Debit Card'));
    expect(screen.getByPlaceholderText('e.g. 4111111111111111')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('MM/YY')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('123')).toBeInTheDocument();
  });

  it('hides bank fields when card payment is selected', () => {
    renderPage();
    fireEvent.click(screen.getByText('Credit / Debit Card'));
    expect(screen.queryByPlaceholderText('e.g. Maybank')).not.toBeInTheDocument();
  });

  it('shows error when online banking fields are empty', async () => {
    const { toast } = await import('sonner');
    renderPage();
    fireEvent.click(screen.getByText('Pay Now'));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please fill in all bank details');
    });
  });

  it('shows error when card fields are empty', async () => {
    const { toast } = await import('sonner');
    renderPage();
    fireEvent.click(screen.getByText('Credit / Debit Card'));
    fireEvent.click(screen.getByText('Pay Now'));
    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Please fill in all card details');
    });
  });

  it('submits online banking payment successfully', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.payOrder.mockResolvedValueOnce({});

    renderPage();
    fireEvent.change(screen.getByPlaceholderText('e.g. Maybank'), {
      target: { value: 'Maybank' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. 1234567890'), {
      target: { value: '1234567890' },
    });
    fireEvent.click(screen.getByText('Pay Now'));

    await waitFor(() => {
      expect(orderApi.payOrder).toHaveBeenCalledWith({
        orderId: 'test-order-123',
        body: {
          paymentMethod: 'online_banking',
          outcome: 'success',
          bankName: 'Maybank',
          accountNumber: '1234567890',
        },
      });
      expect(mockNavigate).toHaveBeenCalledWith('/checkout/confirmation?orderId=test-order-123');
    });
  });

  it('submits card payment successfully', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.payOrder.mockResolvedValueOnce({});

    renderPage();
    fireEvent.click(screen.getByText('Credit / Debit Card'));
    fireEvent.change(screen.getByPlaceholderText('e.g. 4111111111111111'), {
      target: { value: '4111111111111111' },
    });
    fireEvent.change(screen.getByPlaceholderText('MM/YY'), {
      target: { value: '12/25' },
    });
    fireEvent.change(screen.getByPlaceholderText('123'), {
      target: { value: '123' },
    });
    fireEvent.click(screen.getByText('Pay Now'));

    await waitFor(() => {
      expect(orderApi.payOrder).toHaveBeenCalledWith({
        orderId: 'test-order-123',
        body: {
          paymentMethod: 'card',
          outcome: 'success',
          cardNumber: '4111111111111111',
          expiryDate: '12/25',
          cvv: '123',
        },
      });
      expect(mockNavigate).toHaveBeenCalledWith('/checkout/confirmation?orderId=test-order-123');
    });
  });

  it('shows error toast when payment fails', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    const { toast } = await import('sonner');
    orderApi.payOrder.mockRejectedValueOnce(new Error('Payment failed'));

    renderPage();
    fireEvent.change(screen.getByPlaceholderText('e.g. Maybank'), {
      target: { value: 'Maybank' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. 1234567890'), {
      target: { value: '1234567890' },
    });
    fireEvent.click(screen.getByText('Pay Now'));

    await waitFor(() => {
      expect(toast.error).toHaveBeenCalledWith('Payment failed');
    });
  });

  it('shows processing state while payment is in progress', async () => {
    const { orderApi } = await import('@/lib/apiClient');
    orderApi.payOrder.mockImplementation(() => new Promise((resolve) => setTimeout(resolve, 5000)));

    renderPage();
    fireEvent.change(screen.getByPlaceholderText('e.g. Maybank'), {
      target: { value: 'Maybank' },
    });
    fireEvent.change(screen.getByPlaceholderText('e.g. 1234567890'), {
      target: { value: '1234567890' },
    });
    fireEvent.click(screen.getByText('Pay Now'));
    expect(screen.getByText('Processing...')).toBeInTheDocument();
  });

  it('shows invalid order when orderId is missing', () => {
    mockSearchParams.delete('orderId');
    renderPage();
    expect(screen.getByText('Invalid Order')).toBeInTheDocument();
    expect(screen.getByText('Return to Checkout')).toBeInTheDocument();
  });
});
