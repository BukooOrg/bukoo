import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AuthorNewPage from '@/pages/admin/catalog/AuthorNewPage';

vi.mock('@/lib/apiClient', () => ({
  authorApi: {
    createAuthor: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('AuthorNewPage', () => {
  let authorApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    authorApi = mod.authorApi;
    authorApi.createAuthor.mockResolvedValue({ data: { id: 'author-new', name: 'Test Author' } });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Author')).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Authors')).toBeInTheDocument();
    });
  });

  it('renders name input', async () => {
    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Jane Austen/i)).toBeInTheDocument();
    });
  });

  it('shows error when submitting with empty name', async () => {
    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Create Author')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Create Author');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Author name is required')).toBeInTheDocument();
    });
  });

  it('creates an author successfully', async () => {
    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Jane Austen/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Jane Austen/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Author' } });
    });

    const submitButton = screen.getByText('Create Author');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(authorApi.createAuthor).toHaveBeenCalledWith({
        createAuthorRequest: {
          name: 'Test Author',
        },
      });
    });
  });

  it('shows error on API failure', async () => {
    authorApi.createAuthor.mockRejectedValueOnce(new Error('API error'));

    render(
      <MemoryRouter>
        <AuthorNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Jane Austen/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Jane Austen/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Author' } });
    });

    const submitButton = screen.getByText('Create Author');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('API error')).toBeInTheDocument();
    });
  });
});
