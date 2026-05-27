import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import BookNewPage from '@/pages/admin/catalog/BookNewPage';

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    createBook: vi.fn().mockResolvedValue({ data: { id: 'new-book', title: 'New Title' } }),
  },
  uploadBookCover: vi.fn().mockResolvedValue({ data: {} }),
  publisherApi: {
    findPublishers: vi.fn().mockResolvedValue({
      data: {
        items: [
          { id: 'p1', name: 'Penguin' },
          { id: 'p2', name: 'Scribner' },
        ],
      },
    }),
  },
  categoryApi: {
    findCategories: vi.fn().mockResolvedValue({
      data: [
        { id: 'c1', name: 'Fiction' },
        { id: 'c2', name: 'Non-Fiction' },
      ],
    }),
  },
  authorApi: {
    findAuthors: vi.fn().mockResolvedValue({
      data: {
        items: [
          { id: 'a1', name: 'Jane Austen' },
          { id: 'a2', name: 'Charles Dickens' },
        ],
      },
    }),
  },
}));

describe('BookNewPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Book')).toBeInTheDocument();
    });
  });

  it('renders back to books link', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Books')).toBeInTheDocument();
    });
  });

  it('renders title input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter book title')).toBeInTheDocument();
    });
  });

  it('renders price input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('29.99')).toBeInTheDocument();
    });
  });

  it('renders stock input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('1')).toBeInTheDocument();
    });
  });

  it('renders language input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('English')).toBeInTheDocument();
    });
  });

  it('renders ISBN input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('9781234567897')).toBeInTheDocument();
    });
  });

  it('renders cover image input', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Cover Image')).toBeInTheDocument();
    });
  });

  it('renders description textarea', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('A brief description of the book...')).toBeInTheDocument();
    });
  });

  it('renders publisher select with options', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Penguin')).toBeInTheDocument();
      expect(screen.getByText('Scribner')).toBeInTheDocument();
    });
  });

  it('renders category select with options', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fiction')).toBeInTheDocument();
      expect(screen.getByText('Non-Fiction')).toBeInTheDocument();
    });
  });

  it('renders author checkboxes', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Austen')).toBeInTheDocument();
      expect(screen.getByText('Charles Dickens')).toBeInTheDocument();
    });
  });

  it('renders create button', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create book/i })).toBeInTheDocument();
    });
  });

  it('shows validation error when submitting empty title', async () => {
    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /create book/i })).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole('button', { name: /create book/i }));

    await waitFor(() => {
      expect(screen.getByText('Title is required')).toBeInTheDocument();
    });
  });

  it('creates book on valid submit', async () => {
    const { bookApi } = await import('@/lib/apiClient');

    render(
      <MemoryRouter>
        <BookNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText('Enter book title')).toBeInTheDocument();
    });

    fireEvent.change(screen.getByPlaceholderText('Enter book title'), {
      target: { value: 'Test Book' },
    });
    fireEvent.change(screen.getByPlaceholderText('29.99'), { target: { value: '19.99' } });
    fireEvent.change(screen.getByPlaceholderText('1'), { target: { value: '10' } });

    fireEvent.click(screen.getByRole('button', { name: /create book/i }));

    await waitFor(() => {
      expect(bookApi.createBook).toHaveBeenCalledWith(
        expect.objectContaining({
          createBookRequest: expect.objectContaining({
            title: 'Test Book',
            price: '19.99',
            stockQuantity: 10,
          }),
        })
      );
    });
  });
});
