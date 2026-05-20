import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AuthorDetailPage from '@/pages/admin/catalog/AuthorDetailPage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ authorId: 'author-1' }),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/lib/apiClient', () => ({
  authorApi: {
    viewAuthorDetail: vi.fn(),
    updateAuthor: vi.fn(),
    softDeleteAuthor: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockAuthor = {
  id: 'author-1',
  name: 'Jane Austen',
  createdAt: '2024-01-10T08:00:00Z',
};

describe('AuthorDetailPage', () => {
  let authorApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    authorApi = mod.authorApi;
    authorApi.viewAuthorDetail.mockResolvedValue({ data: mockAuthor });
    authorApi.updateAuthor.mockResolvedValue({ data: {} });
    authorApi.softDeleteAuthor.mockResolvedValue({ data: {} });
  });

  it('renders author name', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Jane Austen');
    });
  });

  it('renders created date', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/10 January 2024/)).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Authors')).toBeInTheDocument();
    });
  });

  it('renders edit button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Author')).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete Author')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    authorApi.viewAuthorDetail.mockRejectedValueOnce(new Error('Not found'));

    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load author')).toBeInTheDocument();
    });
  });

  it('opens edit dialog when edit button clicked', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Author');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Author')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit author/i })).toBeInTheDocument();
    });
  });

  it('updates author successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Author');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Author')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit author/i })).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Jane Austen');
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Updated Author' } });
    });

    const saveButton = screen.getByText('Save Changes');
    await act(async () => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(authorApi.updateAuthor).toHaveBeenCalled();
    });

    const callArgs = authorApi.updateAuthor.mock.calls[0][0];
    expect(callArgs.authorId).toBe('author-1');
    expect(callArgs.updateAuthorRequest.name).toBe('Updated Author');
  });

  it('deletes author successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/authors/author-1']}>
        <AuthorDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete Author');
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    const deleteButton = screen.getAllByText('Delete Author')[0];
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Author?')).toBeInTheDocument();
    });

    const confirmButton = screen.getAllByText('Delete Author')[1];
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(authorApi.softDeleteAuthor).toHaveBeenCalledWith({ authorId: 'author-1' });
    });
  });
});
