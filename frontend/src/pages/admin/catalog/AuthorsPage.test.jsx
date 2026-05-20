import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AuthorsPage from '@/pages/admin/catalog/AuthorsPage';

vi.mock('@/lib/apiClient', () => ({
  authorApi: {
    findAuthors: vi.fn(),
    softDeleteAuthor: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockAuthors = [
  {
    id: 'author-1',
    name: 'Jane Austen',
    createdAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'author-2',
    name: 'Charles Dickens',
    createdAt: '2024-02-15T09:00:00Z',
  },
  {
    id: 'author-3',
    name: 'George Orwell',
    createdAt: '2024-03-01T12:00:00Z',
  },
];

function mockAuthorResponse(items, totalItems) {
  return {
    data: {
      items,
      pagination: {
        page: 1,
        pageSize: 20,
        totalItems,
        totalPages: Math.ceil(totalItems / 20) || 1,
        hasNext: false,
        hasPrev: false,
      },
    },
  };
}

describe('AuthorsPage', () => {
  let authorApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    authorApi = mod.authorApi;
    authorApi.findAuthors.mockResolvedValue(mockAuthorResponse(mockAuthors, mockAuthors.length));
    authorApi.softDeleteAuthor.mockResolvedValue({ data: {} });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Authors')).toBeInTheDocument();
    });
  });

  it('renders total author count', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('3 authors total')).toBeInTheDocument();
    });
  });

  it('renders new author button', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Author')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search authors/i)).toBeInTheDocument();
    });
  });

  it('renders all author names in table', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Austen')).toBeInTheDocument();
      expect(screen.getByText('Charles Dickens')).toBeInTheDocument();
      expect(screen.getByText('George Orwell')).toBeInTheDocument();
    });
  });

  it('shows empty state when no authors', async () => {
    authorApi.findAuthors.mockResolvedValueOnce(mockAuthorResponse([], 0));

    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No authors found')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    authorApi.findAuthors.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load authors')).toBeInTheDocument();
    });
  });

  it('searches authors when typing in search input', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search authors/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search authors/i);

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'jane' } });
    });

    await waitFor(
      () => {
        const calls = authorApi.findAuthors.mock.calls;
        const lastCall = calls[calls.length - 1][0];
        expect(lastCall.search).toBe('jane');
      },
      { timeout: 2000 }
    );
  });

  it('deletes an author', async () => {
    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Jane Austen')).toBeInTheDocument();
    });

    const janeRow = screen.getByText('Jane Austen').closest('tr');
    const buttons = janeRow.querySelectorAll('button');
    const deleteButton = buttons[buttons.length - 1];

    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Author?')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Delete Author');
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(authorApi.softDeleteAuthor).toHaveBeenCalledWith({ authorId: 'author-1' });
    });
  });

  it('renders view button for each author', async () => {
    const { container } = render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const viewLinks = container.querySelectorAll('a[href^="/admin/authors/"]');
      expect(viewLinks.length).toBeGreaterThanOrEqual(mockAuthors.length);
    });
  });

  it('renders pagination when total pages > 1', async () => {
    const manyAuthors = Array.from({ length: 25 }, (_, i) => ({
      id: `author-${i}`,
      name: `Author ${i + 1}`,
      createdAt: '2024-01-10T08:00:00Z',
    }));

    authorApi.findAuthors.mockResolvedValue(mockAuthorResponse(manyAuthors.slice(0, 20), 25));

    render(
      <MemoryRouter>
        <AuthorsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
    });

    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
