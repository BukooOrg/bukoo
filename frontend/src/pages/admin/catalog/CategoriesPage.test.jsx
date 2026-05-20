import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CategoriesPage from '@/pages/admin/catalog/CategoriesPage';

vi.mock('@/lib/apiClient', () => ({
  categoryApi: {
    findCategories: vi.fn(),
    softDeleteCategory: vi.fn(),
  },
  collectionApi: {
    findCollections: vi.fn(),
  },
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}));

const mockCategories = [
  {
    id: 'cat-1',
    name: 'Fiction',
    urlSlug: 'fiction',
    collectionId: 'col-1',
    createdAt: '2024-01-10T08:00:00Z',
    updatedAt: '2024-01-10T08:00:00Z',
  },
  {
    id: 'cat-2',
    name: 'Non-Fiction',
    urlSlug: 'non-fiction',
    collectionId: 'col-1',
    createdAt: '2024-02-15T09:00:00Z',
    updatedAt: '2024-02-15T09:00:00Z',
  },
  {
    id: 'cat-3',
    name: 'Science Fiction',
    urlSlug: 'science-fiction',
    collectionId: 'col-2',
    createdAt: '2024-03-01T12:00:00Z',
    updatedAt: '2024-03-01T12:00:00Z',
  },
];

const mockCollections = [
  { id: 'col-1', name: 'Main Collection' },
  { id: 'col-2', name: 'Special Collection' },
];

function mockCategoryResponse(items) {
  return { data: items };
}

function mockCollectionResponse(items) {
  return { data: { items } };
}

describe('CategoriesPage', () => {
  let categoryApi;
  let collectionApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    categoryApi = mod.categoryApi;
    collectionApi = mod.collectionApi;
    categoryApi.findCategories.mockResolvedValue(mockCategoryResponse(mockCategories));
    collectionApi.findCollections.mockResolvedValue(mockCollectionResponse(mockCollections));
    categoryApi.softDeleteCategory.mockResolvedValue({ data: {} });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Categories')).toBeInTheDocument();
    });
  });

  it('renders total category count', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('3 categories total')).toBeInTheDocument();
    });
  });

  it('renders new category button', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Category')).toBeInTheDocument();
    });
  });

  it('renders all category names in table', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fiction')).toBeInTheDocument();
      expect(screen.getByText('Non-Fiction')).toBeInTheDocument();
      expect(screen.getByText('Science Fiction')).toBeInTheDocument();
    });
  });

  it('renders category slugs', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('fiction')).toBeInTheDocument();
      expect(screen.getByText('non-fiction')).toBeInTheDocument();
    });
  });

  it('shows empty state when no categories', async () => {
    categoryApi.findCategories.mockResolvedValueOnce(mockCategoryResponse([]));

    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('No categories found')).toBeInTheDocument();
    });
  });

  it('shows error state on API failure', async () => {
    categoryApi.findCategories.mockRejectedValueOnce(new Error('Network error'));

    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Failed to load categories')).toBeInTheDocument();
    });
  });

  it('filters by collection when collection tab clicked', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Fiction')).toBeInTheDocument();
    });

    const collectionTabs = screen.getAllByRole('button');
    const specialTab = collectionTabs.find((btn) => btn.textContent === 'Special Collection');

    expect(specialTab).toBeTruthy();

    await act(async () => {
      fireEvent.click(specialTab);
    });

    await waitFor(() => {
      const calls = categoryApi.findCategories.mock.calls;
      const lastCall = calls[calls.length - 1][0];
      expect(lastCall.collectionId).toBe('col-2');
    });
  });

  it('deletes a category', async () => {
    render(
      <MemoryRouter>
        <CategoriesPage />
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
      expect(screen.getByText('Delete Category?')).toBeInTheDocument();
    });

    const confirmButton = screen.getByText('Delete Category');
    await act(async () => {
      fireEvent.click(confirmButton);
    });

    await waitFor(() => {
      expect(categoryApi.softDeleteCategory).toHaveBeenCalledWith({ categoryId: 'cat-1' });
    });
  });

  it('renders view button for each category', async () => {
    const { container } = render(
      <MemoryRouter>
        <CategoriesPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      const viewLinks = container.querySelectorAll('a[href^="/admin/categories/"]');
      expect(viewLinks.length).toBeGreaterThanOrEqual(mockCategories.length);
    });
  });
});
