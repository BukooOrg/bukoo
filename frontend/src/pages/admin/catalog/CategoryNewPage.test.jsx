import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import CategoryNewPage from '@/pages/admin/catalog/CategoryNewPage';

vi.mock('@/lib/apiClient', () => ({
  categoryApi: {
    createCategory: vi.fn(),
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

const mockCollections = [
  { id: 'col-1', name: 'Main Collection' },
  { id: 'col-2', name: 'Special Collection' },
];

function mockCollectionResponse(items) {
  return { data: { items } };
}

describe('CategoryNewPage', () => {
  let categoryApi;
  let collectionApi;

  beforeEach(async () => {
    vi.clearAllMocks();
    const mod = await import('@/lib/apiClient');
    categoryApi = mod.categoryApi;
    collectionApi = mod.collectionApi;
    collectionApi.findCollections.mockResolvedValue(mockCollectionResponse(mockCollections));
    categoryApi.createCategory.mockResolvedValue({ data: { id: 'cat-new' } });
  });

  it('renders page header', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('New Category')).toBeInTheDocument();
    });
  });

  it('renders back link', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Back to Categories')).toBeInTheDocument();
    });
  });

  it('renders name input', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Science Fiction/i)).toBeInTheDocument();
    });
  });

  it('renders slug input', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/science-fiction/i)).toBeInTheDocument();
    });
  });

  it('renders collection select', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Select a collection')).toBeInTheDocument();
    });
  });

  it('auto-generates slug from name', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Science Fiction/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Science Fiction/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'My New Category' } });
    });

    const slugInput = screen.getByPlaceholderText(/science-fiction/i);
    expect(slugInput.value).toBe('my-new-category');
  });

  it('shows error when submitting with empty fields', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('Create Category')).toBeInTheDocument();
    });

    const submitButton = screen.getByText('Create Category');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Category name is required')).toBeInTheDocument();
    });
  });

  it('creates a category successfully', async () => {
    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Science Fiction/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Science Fiction/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Category' } });
    });

    const collectionSelect = screen.getByRole('combobox');
    await act(async () => {
      fireEvent.change(collectionSelect, { target: { value: 'col-1' } });
    });

    const submitButton = screen.getByText('Create Category');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(categoryApi.createCategory).toHaveBeenCalledWith({
        createCategoryRequest: {
          name: 'Test Category',
          urlSlug: 'test-category',
          collectionId: 'col-1',
        },
      });
    });
  });

  it('shows error on API failure', async () => {
    categoryApi.createCategory.mockRejectedValueOnce(new Error('API error'));

    render(
      <MemoryRouter>
        <CategoryNewPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/e\.g\. Science Fiction/i)).toBeInTheDocument();
    });

    const nameInput = screen.getByPlaceholderText(/e\.g\. Science Fiction/i);
    await act(async () => {
      fireEvent.change(nameInput, { target: { value: 'Test Category' } });
    });

    const collectionSelect = screen.getByRole('combobox');
    await act(async () => {
      fireEvent.change(collectionSelect, { target: { value: 'col-1' } });
    });

    const submitButton = screen.getByText('Create Category');
    await act(async () => {
      fireEvent.click(submitButton);
    });

    await waitFor(() => {
      expect(screen.getByText('API error')).toBeInTheDocument();
    });
  });
});
