import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CategoryDetailPage from '@/pages/admin/catalog/CategoryDetailPage';

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useParams: () => ({ categoryId: 'cat-1' }),
    useNavigate: () => vi.fn(),
  };
});

vi.mock('@/lib/apiClient', () => ({
  categoryApi: {
    viewCategoryDetail: vi.fn(),
    updateCategory: vi.fn(),
    softDeleteCategory: vi.fn(),
  },
  collectionApi: {
    findCollections: vi.fn(),
  },
  bookApi: {
    findBooks: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockCategory = {
  id: 'cat-1',
  name: 'Fiction',
  urlSlug: 'fiction',
  collectionId: 'col-1',
  createdAt: '2024-01-10T08:00:00Z',
  updatedAt: '2024-06-15T10:00:00Z',
};

const mockCollections = [
  { id: 'col-1', name: 'Main Collection' },
  { id: 'col-2', name: 'Special Collection' },
];

describe('CategoryDetailPage', () => {
  let categoryApi;
  let collectionApi;
  let bookApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    categoryApi = mod.categoryApi;
    collectionApi = mod.collectionApi;
    bookApi = mod.bookApi;
    categoryApi.viewCategoryDetail.mockResolvedValue({ data: mockCategory });
    collectionApi.findCollections.mockResolvedValue({ data: mockCollections });
    categoryApi.updateCategory.mockResolvedValue({ data: {} });
    categoryApi.softDeleteCategory.mockResolvedValue({ data: {} });
    bookApi.findBooks.mockResolvedValue({ data: { items: [] } });
  });

  it('renders category name', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const heading = screen.getByRole('heading', { level: 1 });
      expect(heading).toHaveTextContent('Fiction');
    });
  });

  it('renders category slug', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const slugElements = screen.getAllByText('fiction');
      expect(slugElements.length).toBeGreaterThan(0);
    });
  });

  it('renders collection name', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Main Collection')).toBeInTheDocument();
    });
  });

  it('renders created date', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/10 January 2024/)).toBeInTheDocument();
    });
  });

  it('renders last updated date', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/15 June 2024/)).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Categories')).toBeInTheDocument();
    });
  });

  it('renders edit button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Edit Category')).toBeInTheDocument();
    });
  });

  it('renders delete button', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Delete Category')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    categoryApi.viewCategoryDetail.mockRejectedValueOnce(new Error('Not found'));

    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load category')).toBeInTheDocument();
    });
  });

  it('opens edit dialog when edit button clicked', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Category');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Category')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit category/i })).toBeInTheDocument();
    });
  });

  it('updates category successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const editButtons = screen.getAllByText('Edit Category');
      expect(editButtons.length).toBeGreaterThan(0);
    });

    const editButton = screen.getAllByText('Edit Category')[0];
    await act(async () => {
      fireEvent.click(editButton);
    });

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /edit category/i })).toBeInTheDocument();
    });

    const nameInput = screen.getByDisplayValue('Fiction');
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Updated Fiction' } });
    });

    const saveButton = screen.getByText('Save Changes');
    await act(async () => {
      fireEvent.click(saveButton);
    });

    await waitFor(() => {
      expect(categoryApi.updateCategory).toHaveBeenCalled();
    });

    console.log('Mock calls:', categoryApi.updateCategory.mock.calls);
    const callArgs = categoryApi.updateCategory.mock.calls[0][0];
    expect(callArgs.categoryId).toBe('cat-1');
    expect(callArgs.createCategoryRequest.name).toBe('Updated Fiction');
    expect(callArgs.createCategoryRequest.collectionId).toBe('col-1');
  });

  it('deletes category successfully', async () => {
    render(
      <MemoryRouter initialEntries={['/admin/categories/cat-1']}>
        <CategoryDetailPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete Category');
      expect(deleteButtons.length).toBeGreaterThan(0);
    });

    const deleteButton = screen.getAllByText('Delete Category')[0];
    await act(async () => {
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Delete Category?')).toBeInTheDocument();
    });

    const confirmButton = screen.getAllByText('Delete Category')[1];
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(categoryApi.softDeleteCategory).toHaveBeenCalledWith({ categoryId: 'cat-1' });
    });
  });
});
