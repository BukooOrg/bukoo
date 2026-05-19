import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import BooksPage from '@/pages/admin/catalog/BooksPage';

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    findBooks: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 'book-1',
            title: 'The Great Gatsby',
            price: '15.99',
            stockQuantity: 50,
            isActive: true,
            coverUrl: null,
            authors: [{ id: 'a1', name: 'F. Scott Fitzgerald', displayOrder: 1 }],
            publisher: { id: 'p1', name: 'Scribner' },
            category: { id: 'c1', name: 'Classics' },
            createdAt: '2024-01-01',
            updatedAt: '2024-06-01',
          },
          {
            id: 'book-2',
            title: '1984',
            price: '12.99',
            stockQuantity: 0,
            isActive: false,
            coverUrl: 'https://example.com/1984.jpg',
            authors: [{ id: 'a2', name: 'George Orwell', displayOrder: 1 }],
            publisher: null,
            category: null,
            createdAt: '2024-02-01',
            updatedAt: '2024-05-01',
          },
        ],
        pagination: {
          page: 1,
          pageSize: 20,
          totalItems: 2,
          totalPages: 1,
          hasNext: false,
          hasPrev: false,
        },
      },
    }),
    deactivateBook: vi.fn().mockResolvedValue({ data: {} }),
    activateBook: vi.fn().mockResolvedValue({ data: {} }),
    softDeleteBook: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

describe('BooksPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Books')).toBeInTheDocument();
    });
  });

  it('renders new book button', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Book')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search books/i)).toBeInTheDocument();
    });
  });

  it('renders book titles in table', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('The Great Gatsby')).toBeInTheDocument();
      expect(screen.getByText('1984')).toBeInTheDocument();
    });
  });

  it('renders book prices', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/RM\s*15\.99/)).toBeInTheDocument();
      expect(screen.getByText(/RM\s*12\.99/)).toBeInTheDocument();
    });
  });

  it('renders stock quantities', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('50')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
    });
  });

  it('renders author names', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('F. Scott Fitzgerald')).toBeInTheDocument();
      expect(screen.getByText('George Orwell')).toBeInTheDocument();
    });
  });

  it('renders active badge for active books', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument();
    });
  });

  it('renders inactive badge for deactivated books', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Inactive')).toBeInTheDocument();
    });
  });

  it('renders publisher name', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Scribner')).toBeInTheDocument();
    });
  });

  it('shows empty state when no books', async () => {
    const { bookApi } = await import('@/lib/apiClient');
    bookApi.findBooks.mockResolvedValueOnce({
      data: {
        items: [],
        pagination: {
          page: 1,
          pageSize: 20,
          totalItems: 0,
          totalPages: 0,
          hasNext: false,
          hasPrev: false,
        },
      },
    });

    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No books found')).toBeInTheDocument();
    });
  });

  it('renders total book count', async () => {
    render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('2 books total')).toBeInTheDocument();
    });
  });

  it('renders edit buttons for each book', async () => {
    const { container } = render(
      <MemoryRouter>
        <BooksPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editLinks = container.querySelectorAll('a[href^="/admin/books/"]');
      expect(editLinks.length).toBeGreaterThanOrEqual(2);
    });
  });
});
