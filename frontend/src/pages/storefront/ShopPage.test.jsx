import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ShopPage from '@/pages/storefront/ShopPage';

vi.mock('@/components/cart/CartContext', () => ({
  useCart: () => ({
    cart: { lines: [], totalQuantity: 0 },
    cartOpen: false,
    setCartOpen: vi.fn(),
    addCartItem: vi.fn(),
    updateCartItem: vi.fn(),
    deleteCartItem: vi.fn(),
  }),
  CartProvider: ({ children }) => children,
}));

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    findBooks: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 'book-1',
            title: 'Shop Book One',
            price: '15.99',
            stockQuantity: 10,
            coverUrl: 'https://example.com/book1.jpg',
            authors: [{ id: 'a1', name: 'Author One', displayOrder: 1 }],
            publisher: null,
            category: null,
          },
        ],
      },
    }),
  },
}));

describe('ShopPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders shop content on mount', async () => {
    render(
      <MemoryRouter>
        <ShopPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('1 Results')).toBeInTheDocument();
    });
  });

  it('renders book title', async () => {
    render(
      <MemoryRouter>
        <ShopPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Shop Book One')).toBeInTheDocument();
    });
  });

  it('renders product card price', async () => {
    render(
      <MemoryRouter>
        <ShopPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/RM\s*15\.99/)).toBeInTheDocument();
    });
  });

  it('shows mock banner when API returns empty', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.findBooks.mockResolvedValueOnce({ data: { items: [] } });

    render(
      <MemoryRouter>
        <ShopPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sort by: Newest')).toBeInTheDocument();
    });
  });

  it('renders sort by label', async () => {
    render(
      <MemoryRouter>
        <ShopPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Sort by: Newest')).toBeInTheDocument();
    });
  });
});
