import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import AccountReviewsPage from '@/pages/account/ReviewsPage';

vi.mock('@/lib/apiClient', () => ({
  userApi: {
    findMyReviews: vi.fn(),
    updateMyReview: vi.fn(),
    softDeleteMyReview: vi.fn(),
  },
}));

vi.mock('@/context/AuthContext', () => ({
  useAuth: () => ({ user: { id: 'user-1', fullName: 'Test User', email: 'test@example.com' } }),
}));

const mockReviews = [
  {
    id: 'review-1',
    book_id: 'book-1',
    rating: 4,
    comment: 'Great book, really enjoyed it!',
    is_hidden: false,
    created_at: '2024-01-15T10:00:00Z',
    updated_at: '2024-01-15T10:00:00Z',
    book: { id: 'book-1', title: 'The Great Novel' },
  },
  {
    id: 'review-2',
    book_id: 'book-2',
    rating: 5,
    comment: 'Absolutely amazing!',
    is_hidden: false,
    created_at: '2024-02-20T14:30:00Z',
    updated_at: '2024-02-20T14:30:00Z',
    book: { id: 'book-2', title: 'Another Good Read' },
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
      <AccountReviewsPage />
    </MemoryRouter>
  );
}

describe('AccountReviewsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('shows loading spinner initially', () => {
    renderPage();
    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('shows reviews list after loading', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('My Reviews')).toBeInTheDocument();
    });
  });

  it('shows review comments', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Great book, really enjoyed it!')).toBeInTheDocument();
    });
  });

  it('shows book titles as links', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('The Great Novel')).toBeInTheDocument();
      expect(screen.getByText('Another Good Read')).toBeInTheDocument();
    });
  });

  it('shows empty state when no reviews', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce({
      data: { items: [], meta: { totalPages: 1 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('No Reviews Yet')).toBeInTheDocument();
      expect(screen.getByText('Browse Books')).toBeInTheDocument();
    });
  });

  it('shows pagination when multiple pages', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce({
      data: { items: mockReviews, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Page 1 of 3')).toBeInTheDocument();
    });
  });

  it('navigates to next page', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValue({
      data: { items: mockReviews, meta: { totalPages: 3 } },
    });

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('Next')).not.toBeDisabled();
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(userApi.findMyReviews).toHaveBeenCalledWith(expect.objectContaining({ page: 2 }));
    });
  });

  it('has action buttons for each review', async () => {
    const { userApi } = await import('@/lib/apiClient');
    userApi.findMyReviews.mockResolvedValueOnce(mockPaginatedResponse);

    renderPage();

    await waitFor(() => {
      expect(screen.getByText('My Reviews')).toBeInTheDocument();
    });

    // Each review should have an actions button
    const actionButtons = screen.getAllByRole('button', { name: /review actions/i });
    expect(actionButtons.length).toBeGreaterThanOrEqual(2);
  });
});
