import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CollectionDetailPage from '@/pages/admin/catalog/CollectionDetailPage';

vi.mock('@/lib/apiClient', () => ({
  collectionApi: {
    viewCollectionDetailApiAppV1CollectionsCollectionIdGet: vi.fn(),
    updateCollectionApiAppV1CollectionsCollectionIdPatch: vi.fn(),
    softDeleteCollection: vi.fn(),
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
    useParams: () => ({ collectionId: 'col-1' }),
  };
});

const mockCollection = {
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
    {
      id: 'cat-2',
      name: 'Mystery',
      urlSlug: 'mystery',
      collectionId: 'col-1',
      createdAt: '2024-02-10T10:00:00Z',
    },
  ],
  createdAt: '2024-01-10T08:00:00Z',
};

function mockDetailResponse(item) {
  return { data: item };
}

describe('CollectionDetailPage', () => {
  let collectionApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    mockNavigate.mockReset();
    const mod = await import('@/lib/apiClient');
    collectionApi = mod.collectionApi;
    collectionApi.viewCollectionDetailApiAppV1CollectionsCollectionIdGet.mockResolvedValue(
      mockDetailResponse(mockCollection)
    );
    collectionApi.updateCollectionApiAppV1CollectionsCollectionIdPatch.mockResolvedValue({
      data: { ...mockCollection, name: 'Updated Fiction' },
    });
    collectionApi.softDeleteCollection.mockResolvedValue({ data: {} });
  });

  it('renders collection name', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('Fiction').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders url slug', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('fiction').length).toBeGreaterThanOrEqual(1);
    });
  });

  it('renders category count', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('2')).toBeInTheDocument();
    });
  });

  it('renders categories list', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Literary Fiction')).toBeInTheDocument();
      expect(screen.getByText('Mystery')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    collectionApi.viewCollectionDetailApiAppV1CollectionsCollectionIdGet.mockRejectedValueOnce(
      new Error('Network error')
    );

    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load collection')).toBeInTheDocument();
    });
  });

  it('renders edit button', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Collection')).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete Collection')).toBeInTheDocument();
    });
  });

  it('opens edit dialog and updates collection', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Collection')).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit collection/i });
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Fiction');
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Updated Fiction' } });
    });

    const saveButton = screen.getByRole('button', { name: /save changes/i });
    await act(async () => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(
        collectionApi.updateCollectionApiAppV1CollectionsCollectionIdPatch
      ).toHaveBeenCalledWith({
        collectionId: 'col-1',
        updateCollectionRequest: {
          name: 'Updated Fiction',
          urlSlug: 'fiction',
        },
      });
    });
  });

  it('deletes a collection', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete Collection')).toBeInTheDocument();
    });

    const deleteButton = screen.getByRole('button', { name: /delete collection/i });
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Collection?')).toBeInTheDocument();
    });

    const confirmButton = screen.getByRole('button', {
      name: /delete collection/i,
      selector: 'button[type="button"]',
    });
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(collectionApi.softDeleteCollection).toHaveBeenCalledWith({ collectionId: 'col-1' });
    });

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/admin/collections');
    });
  });

  it('shows slug input in edit dialog', async () => {
    render(
      <MemoryRouter>
        <CollectionDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Collection')).toBeInTheDocument();
    });

    const editButton = screen.getByRole('button', { name: /edit collection/i });
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('dialog')).toBeInTheDocument();
    });

    const slugInput = screen.getByDisplayValue('fiction');
    expect(slugInput).toBeInTheDocument();
  });
});
