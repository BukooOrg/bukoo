import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import HomePage from '@/pages/storefront/HomePage';

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

vi.mock('@/components/wishlist/WishlistContext', () => ({
  useWishlist: () => ({
    wishlist: [],
    isInWishlist: vi.fn().mockReturnValue(false),
    addToWishlist: vi.fn(),
    removeFromWishlist: vi.fn(),
    toggleWishlist: vi.fn(),
  }),
  WishlistProvider: ({ children }) => children,
}));

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    findBooks: vi.fn(),
  },
}));

vi.mock('@/data/mock/products.json', () => ({
  default: [],
}));

const defaultBooksResponse = {
  data: {
    items: [
      {
        id: 'book-1',
        title: 'Featured Book One',
        price: '19.99',
        stockQuantity: 50,
        coverUrl: 'https://example.com/book1.jpg',
        authors: [{ id: 'a1', name: 'Author One', displayOrder: 1 }],
        publisher: { id: 'p1', name: 'Pub One' },
        category: { id: 'c1', name: 'Fiction' },
      },
      {
        id: 'book-2',
        title: 'Featured Book Two',
        price: '24.99',
        stockQuantity: 0,
        coverUrl: null,
        authors: [],
        publisher: null,
        category: null,
      },
    ],
  },
};

describe('HomePage', () => {
  beforeEach(async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.findBooks.mockReset();
    bookApi.findBooks.mockResolvedValue(defaultBooksResponse);
  });

  it('renders book titles', async () => {
    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Featured Book One')).toBeInTheDocument();
      expect(screen.getByText('Featured Book Two')).toBeInTheDocument();
    });
  });

  it('renders product cards as links', async () => {
    const { container } = render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const links = container.querySelectorAll('a[href^="/product/"]');
      expect(links.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('shows empty state when API errors and mock data is empty', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.findBooks.mockRejectedValue(new Error('API error'));

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/shelves.*restocked/i)).toBeInTheDocument();
    });
  });

  it('shows empty state when API returns empty items', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.findBooks.mockResolvedValue({
      data: { items: [], pagination: { totalItems: 0 } },
    });

    render(
      <MemoryRouter>
        <HomePage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/shelves.*restocked/i)).toBeInTheDocument();
    });
  });
});
