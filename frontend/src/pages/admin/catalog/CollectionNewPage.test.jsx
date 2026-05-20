import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CollectionNewPage from '@/pages/admin/catalog/CollectionNewPage';

vi.mock('@/lib/apiClient', () => ({
  collectionApi: {
    createCollection: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockNavigate = vi.fn();

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

describe('CollectionNewPage', () => {
  let collectionApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockNavigate.mockReset();
    const mod = await import('@/lib/apiClient');
    collectionApi = mod.collectionApi;
    collectionApi.createCollection.mockResolvedValue({
      data: {
        id: 'col-new',
        name: 'Test Collection',
        urlSlug: 'test-collection',
        categories: [],
        createdAt: '2024-01-10T08:00:00Z',
      },
    });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Collection')).toBeInTheDocument();
    });
  });

  it('renders back to collections link', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Collections')).toBeInTheDocument();
    });
  });

  it('renders name and url slug inputs', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/fiction books/i)).toBeInTheDocument();
      expect(screen.getByPlaceholderText(/fiction-books/i)).toBeInTheDocument();
    });
  });

  it('auto-generates url slug from name', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText(/fiction books/i);
    const slugInput = screen.getByPlaceholderText(/fiction-books/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Fiction Books' } });
    });

    expect(slugInput.value).toBe('fiction-books');
  });

  it('handles special characters in slug generation', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText(/fiction books/i);
    const slugInput = screen.getByPlaceholderText(/fiction-books/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Science & Fiction: Books!' } });
    });

    expect(slugInput.value).toBe('science-fiction-books');
  });

  it('allows manual editing of url slug', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText(/fiction books/i);
    const slugInput = screen.getByPlaceholderText(/fiction-books/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Fiction Books' } });
    });

    await act(async () => {
      fireEvent.change(slugInput, { target: { value: 'custom-slug' } });
    });

    expect(slugInput.value).toBe('custom-slug');
  });

  it('shows error when name is empty', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const submitButton = screen.getByRole('button', { name: /create collection/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Collection name is required')).toBeInTheDocument();
    });
  });

  it('creates a collection successfully', async () => {
    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText(/fiction books/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Collection' } });
    });

    const submitButton = screen.getByRole('button', { name: /create collection/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(collectionApi.createCollection).toHaveBeenCalledWith({
        createCollectionRequest: {
          name: 'Test Collection',
          urlSlug: 'test-collection',
        },
      });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin/collections/col-new');
    });
  });

  it('shows error on create failure', async () => {
    collectionApi.createCollection.mockRejectedValueOnce(new Error('Duplicate slug'));

    render(
      <MemoryRouter>
        <CollectionNewPage />
      </MemoryRouter>
    );

    const nameInput = screen.getByPlaceholderText(/fiction books/i);

    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Collection' } });
    });

    const submitButton = screen.getByRole('button', { name: /create collection/i });
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Duplicate slug')).toBeInTheDocument();
    });
  });
});
