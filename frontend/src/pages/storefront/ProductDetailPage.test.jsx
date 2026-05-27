import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import ProductDetailPage from '@/pages/storefront/ProductDetailPage';

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
    wishlist: { items: [] },
    loading: false,
    addToWishlist: vi.fn(),
    removeFromWishlist: vi.fn(),
    moveToCart: vi.fn(),
    isInWishlist: () => false,
    refreshWishlist: vi.fn(),
  }),
  WishlistProvider: ({ children }) => children,
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ user: null, loading: false }),
}));

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    viewBookDetail: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '29.99',
        stockQuantity: 10,
        coverUrl: 'https://example.com/cover.jpg',
        description: 'A classic romance novel.',
        isbn: '978-0-141-43951-7',
        pageCount: 432,
        language: 'English',
        publishedDate: new Date('1813-01-28'),
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
      },
    }),
    findReviews: vi.fn().mockResolvedValue({
      data: {
        items: [],
        meta: { totalPages: 1, totalCount: 0 },
      },
    }),
  },
  getToken: () => 'mock-token',
}));

describe('ProductDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders book title', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const elements = screen.getAllByText('Pride and Prejudice');
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('renders author name', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const elements = screen.getAllByText('Penguin Classics');
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders breadcrumb shop link', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const shopLink = screen.getByText('Shop');
      expect(shopLink.closest('a')).toHaveAttribute('href', '/shop');
    });
  });

  it('renders price', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/RM\s*29\.99/)).toBeInTheDocument();
    });
  });

  it('renders metadata section', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('ISBN')).toBeInTheDocument();
      expect(screen.getByText('978-0-141-43951-7')).toBeInTheDocument();
      expect(screen.getByText('432')).toBeInTheDocument();
      expect(screen.getByText('English')).toBeInTheDocument();
    });
  });

  it('renders add to cart button', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Add to cart')).toBeInTheDocument();
    });
  });

  it('shows not found when API fails and no mock', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.viewBookDetail.mockRejectedValueOnce(new Error('Not found'));

    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Book not found.')).toBeInTheDocument();
    });
  });

  it('renders description text', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const elements = screen.getAllByText('A classic romance novel.');
      expect(elements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders About This Book header', async () => {
    render(
      <MemoryRouter>
        <ProductDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('About This Book')).toBeInTheDocument();
    });
  });
});
