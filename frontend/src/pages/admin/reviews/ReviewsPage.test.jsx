import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AdminReviewsPage from '@/pages/admin/reviews/ReviewsPage';

vi.mock('@/lib/apiClient', () => ({
  reviewApi: {
    findReviewsByAdmin: vi.fn(),
    hideOrRestoreReview: vi.fn(),
    softDeleteReview: vi.fn(),
  },
}));

const mockReviews = [
  {
    id: 'review-1',
    book_id: 'book-1',
    user_id: 'user-1',
    rating: 4,
    comment: 'Great book!',
    isHidden: false,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    book: { id: 'book-1', title: 'The Great Novel' },
  },
  {
    id: 'review-2',
    book_id: 'book-2',
    user_id: 'user-2',
    rating: 2,
    comment: 'Not what I expected',
    isHidden: true,
    created_at: '2024-02-20T14:30:00Z',
    updated_at: '2024-02-20T14:30:00Z',
    book: { id: 'book-2', title: 'Another Book' },
  },
];

const mockPaginatedResponse = {
  data: {
    items: mockReviews,
    meta: { totalPages: 1 },
  },
};

function renderPage() {
  return render(
    <MemoryRouter>
      <AdminReviewsPage />
    </MemoryRouter>
  );
}

describe('AdminReviewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows reviews table after loading', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Reviews')).toBeInTheDocument();
    });
  });

  it('shows book titles in table', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('The Great Novel')).toBeInTheDocument();
      expect(screen.getByText('Another Book')).toBeInTheDocument();
    });
  });

  it('shows review comments', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Great book!')).toBeInTheDocument();
    });
  });

  it('shows visible status badge', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Visible')).toBeInTheDocument();
    });
  });

  it('shows hidden status badge', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Hidden')).toBeInTheDocument();
    });
  });

  it('shows empty state when no reviews', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce({
      data: { items: [], meta: { totalPages: 1 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText(/No reviews/i)).toBeInTheDocument();
    });
  });

  it('filters by hidden status', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Reviews')).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'hidden' } });

    await waitFor(() => {
      expect(reviewApi.findReviewsByAdmin).toHaveBeenCalledWith(
        expect.objectContaining({ isHidden: true })
      );
    });
  });

  it('searches reviews', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValue(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Reviews')).toBeInTheDocument();
    });

    const searchInput = screen.getByPlaceholderText('Search reviews...');
    fireEvent.change(searchInput, { target: { value: 'great' } });

    await waitFor(() => {
      expect(reviewApi.findReviewsByAdmin).toHaveBeenCalledWith(
        expect.objectContaining({ search: 'great' })
      );
    });
  });

  it('shows pagination when multiple pages', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValueOnce({
      data: { items: mockReviews, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
  });

  it('navigates to next page', async () => {
    const { reviewApi } = await import('@/lib/apiClient');
    reviewApi.findReviewsByAdmin.mockResolvedValue({
      data: { items: mockReviews, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Next')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(reviewApi.findReviewsByAdmin).toHaveBeenCalledWith(
        expect.objectContaining({ page: 2 })
      );
    });
  });
});
