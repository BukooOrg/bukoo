import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CollectionsPage from '@/pages/admin/catalog/CollectionsPage';

vi.mock('@/lib/apiClient', () => ({
  collectionApi: {
    findCollections: vi.fn(),
    softDeleteCollection: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockCollections = [
  {
    id: 'col-1',
    name: 'Fiction',
    urlSlug: 'fiction',
    categories: [
      {
        id: 'cat-1',
        name: 'Literary Fiction',
        urlSlug: 'literary-fiction',
        collectionId: 'col-1',
        createdAt: '2024-01-15T10:00:00Z',
      },
    ],
    createdAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'col-2',
    name: 'Non-Fiction',
    urlSlug: 'non-fiction',
    categories: [],
    createdAt: '2024-02-15T09:00:00Z',
  },
  {
    id: 'col-3',
    name: 'Children',
    urlSlug: 'children',
    categories: [
      {
        id: 'cat-2',
        name: 'Picture Books',
        urlSlug: 'picture-books',
        collectionId: 'col-3',
        createdAt: '2024-03-01T12:00:00Z',
      },
      {
        id: 'cat-3',
        name: 'Middle Grade',
        urlSlug: 'middle-grade',
        collectionId: 'col-3',
        createdAt: '2024-03-02T12:00:00Z',
      },
    ],
    createdAt: '2024-03-01T12:00:00Z',
  },
];

function mockCollectionResponse(items) {
  return {
    data: items,
  };
}

describe('CollectionsPage', () => {
  let collectionApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    collectionApi = mod.collectionApi;
    collectionApi.findCollections.mockResolvedValue(mockCollectionResponse(mockCollections));
    collectionApi.softDeleteCollection.mockResolvedValue({ data: {} });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Collections')).toBeInTheDocument();
    });
  });

  it('renders total collection count', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('3 collections total')).toBeInTheDocument();
    });
  });

  it('renders new collection button', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Collection')).toBeInTheDocument();
    });
  });

  it('renders search input', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search collections/i)).toBeInTheDocument();
    });
  });

  it('renders all collection names in table', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fiction')).toBeInTheDocument();
      expect(screen.getByText('Non-Fiction')).toBeInTheDocument();
      expect(screen.getByText('Children')).toBeInTheDocument();
    });
  });

  it('renders category counts', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('1')).toBeInTheDocument();
      expect(screen.getByText('0')).toBeInTheDocument();
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('shows empty state when no collections', async () => {
    collectionApi.findCollections.mockResolvedValueOnce(mockCollectionResponse([]));

    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No collections found')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    collectionApi.findCollections.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load collections')).toBeInTheDocument();
    });
  });

  it('filters collections when typing in search input', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/search collections/i)).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText(/search collections/i);

    await act(async () => {
      fireEvent.change(searchInput, { target: { value: 'fiction' } });
    });

    await waitFor(
      () => {
        expect(screen.getByText('Fiction')).toBeInTheDocument();
        expect(screen.getByText('Non-Fiction')).toBeInTheDocument();
        expect(screen.queryByText('Children')).not.toBeInTheDocument();
      },
      { timeout: 2000 }
    );
  });

  it('deletes a collection', async () => {
    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fiction')).toBeInTheDocument();
    });

    const fictionRow = screen.getByText('Fiction').closest('tr');
    const buttons = fictionRow.querySelectorAll('button');
    const deleteButton = buttons[buttons.length - 1];

    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Collection?')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Delete Collection');
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(collectionApi.softDeleteCollection).toHaveBeenCalledWith({ collectionId: 'col-1' });
    });
  });

  it('renders view button for each collection', async () => {
    const { container } = render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const viewLinks = container.querySelectorAll('a[href^="/admin/collections/"]');
      expect(viewLinks.length).toBeGreaterThanOrEqual(mockCollections.length);
    });
  });

  it('renders pagination when total items > 20', async () => {
    const manyCollections = Array.from({ length: 25 }, (_, i) => ({
      id: `col-${i}`,
      name: `Collection ${i + 1}`,
      urlSlug: `collection-${i + 1}`,
      categories: [],
      createdAt: '2024-01-10T08:00:00Z',
    }));

    collectionApi.findCollections.mockResolvedValue(mockCollectionResponse(manyCollections));

    render(
      <MemoryRouter>
        <CollectionsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 2')).toBeInTheDocument();
    });

    expect(screen.getByText('Next')).toBeInTheDocument();
  });
});
