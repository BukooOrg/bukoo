import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import BookDetailPage from '@/pages/admin/catalog/BookDetailPage';

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    viewBookDetail: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: true,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
    updateBook: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: true,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
    updateBookStockQuantity: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: true,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
    deactivateBook: vi.fn().mockResolvedValue({
      data: {
        id: 'book-2',
        title: 'Deactivated Book',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: false,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
    activateBook: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: true,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
    softDeleteBook: vi.fn().mockResolvedValue({ data: {} }),
    uploadBookCover: vi.fn().mockResolvedValue({
      data: {
        id: 'book-1',
        title: 'Pride and Prejudice',
        price: '12.99',
        stockQuantity: 25,
        language: 'English',
        isbn: '978-0-141-43951-7',
        description: 'A classic romance novel.',
        pageCount: 432,
        publishedDate: '1813-01-28',
        isActive: true,
        coverUrl: 'https://example.com/cover.jpg',
        publisher: { id: 'p1', name: 'Penguin Classics' },
        category: { id: 'c1', name: 'Romance' },
        authors: [{ id: 'a1', name: 'Jane Austen', displayOrder: 1 }],
        createdAt: '2024-01-01',
        updatedAt: '2024-06-01',
      },
    }),
  },
  publisherApi: {
    findPublishers: vi.fn().mockResolvedValue({
      data: { items: [{ id: 'p1', name: 'Penguin Classics' }] },
    }),
  },
  categoryApi: {
    findCategories: vi.fn().mockResolvedValue({
      data: [{ id: 'c1', name: 'Romance' }],
    }),
  },
  authorApi: {
    findAuthors: vi.fn().mockResolvedValue({
      data: { items: [{ id: 'a1', name: 'Jane Austen' }] },
    }),
  },
}));

describe('BookDetailPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders book title', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Pride and Prejudice')).toBeInTheDocument();
    });
  });

  it('renders back to books link', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Books')).toBeInTheDocument();
    });
  });

  it('renders active badge for active book', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('renders category name', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const elements = screen.getAllByText('Romance');
      expect(elements.length).toBeGreaterThanOrEqual(2);
    });
  });

  it('renders book price', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/RM\s*12\.99/)).toBeInTheDocument();
    });
  });

  it('renders stock quantity', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('25')).toBeInTheDocument();
    });
  });

  it('renders page count', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('432')).toBeInTheDocument();
    });
  });

  it('renders language', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('English')).toBeInTheDocument();
    });
  });

  it('renders deactivate button for active book', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /deactivate/i })).toBeInTheDocument();
    });
  });

  it('renders edit button', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });
  });

  it('renders stock update input', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('25')).toBeInTheDocument();
    });
  });

  it('enters edit mode when edit is clicked', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /^edit$/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /^edit$/i }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /save changes/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
    });
  });

  it('renders description section', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('A classic romance novel.')).toBeInTheDocument();
    });
  });

  it('renders publisher info with link', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const link = screen.getByText('Penguin Classics');
      expect(link.closest('a')).toHaveAttribute('href', '/admin/publishers/p1');
    });
  });

  it('renders author info with link', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const link = screen.getByText('Jane Austen');
      expect(link.closest('a')).toHaveAttribute('href', '/admin/authors/a1');
    });
  });

  it('shows not found state when book is missing', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.viewBookDetail.mockRejectedValueOnce(new Error('Not found'));

    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Book Not Found')).toBeInTheDocument();
    });
  });

  it('shows delete confirmation dialog', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /delete/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /delete/i }));

    await waitFor(() => {
      expect(screen.getByText('Delete Book')).toBeInTheDocument();
      expect(screen.getByText(/permanently delete/i)).toBeInTheDocument();
    });
  });

  it('renders ISBN in details card', async () => {
    render(
      <MemoryRouter>
        <BookDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('978-0-141-43951-7')).toBeInTheDocument();
    });
  });
});
