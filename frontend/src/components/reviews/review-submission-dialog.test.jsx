import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { ReviewSubmissionDialog } from '@/components/reviews/review-submission-dialog';
import * as apiClient from '@/lib/apiClient';

vi.mock('@/lib/apiClient', () => ({
  bookApi: {
    createReview: vi.fn(),
  },
  userApi: {
    updateMyReview: vi.fn(),
  },
}));

const defaultProps = {
  bookId: 'book-123',
  orderItemId: 'item-456',
  bookTitle: 'Test Book',
  open: true,
  onOpenChange: vi.fn(),
};

describe('ReviewSubmissionDialog', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders dialog with book title when open', () => {
    render(<ReviewSubmissionDialog {...defaultProps} />);
    expect(screen.getByText('Write a Review')).toBeInTheDocument();
    expect(screen.getByText(/Reviewing:/)).toBeInTheDocument();
  });

  it('does not render when open is false', () => {
    render(<ReviewSubmissionDialog {...defaultProps} open={false} />);
    expect(screen.queryByText('Write a Review')).not.toBeInTheDocument();
  });

  it('renders star rating and comment field', () => {
    render(<ReviewSubmissionDialog {...defaultProps} />);
    const stars = screen.getAllByRole('radio');
    expect(stars).toHaveLength(5);
    expect(screen.getByPlaceholderText(/Share your thoughts/)).toBeInTheDocument();
  });

  it('calls bookApi.createReview with correct payload on submit', async () => {
    apiClient.bookApi.createReview.mockResolvedValue({ data: { id: 'review-1' } });

    render(<ReviewSubmissionDialog {...defaultProps} />);

    // Click 4th star
    const stars = screen.getAllByRole('radio');
    fireEvent.click(stars[3]);

    // Fill comment
    const textarea = screen.getByPlaceholderText(/Share your thoughts/);
    fireEvent.change(textarea, { target: { value: 'Great book!' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Submit Review/ }));

    await waitFor(() => {
      expect(apiClient.bookApi.createReview).toHaveBeenCalledWith({
        bookId: 'book-123',
        createReviewRequest: {
          orderItemId: 'item-456',
          rating: 4,
          comment: 'Great book!',
        },
      });
    });
  });

  it('shows success toast and closes dialog on successful submission', async () => {
    apiClient.bookApi.createReview.mockResolvedValue({ data: { id: 'review-1' } });

    const onOpenChange = vi.fn();
    render(<ReviewSubmissionDialog {...defaultProps} onOpenChange={onOpenChange} />);

    const stars = screen.getAllByRole('radio');
    fireEvent.click(stars[2]);
    fireEvent.change(screen.getByPlaceholderText(/Share your thoughts/), {
      target: { value: 'Nice read' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Submit Review/ }));

    await waitFor(() => {
      expect(onOpenChange).toHaveBeenCalledWith(false);
    });
  });

  it('shows error toast on API failure', async () => {
    apiClient.bookApi.createReview.mockRejectedValue(new Error('Review not eligible'));

    render(<ReviewSubmissionDialog {...defaultProps} />);

    const stars = screen.getAllByRole('radio');
    fireEvent.click(stars[1]);
    fireEvent.change(screen.getByPlaceholderText(/Share your thoughts/), {
      target: { value: 'Test comment' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Submit Review/ }));

    await waitFor(() => {
      // Dialog should still be open after error
      expect(screen.getByText('Write a Review')).toBeInTheDocument();
    });
  });

  it('calls onOpenChange(false) when cancel is clicked', () => {
    const onOpenChange = vi.fn();
    render(<ReviewSubmissionDialog {...defaultProps} onOpenChange={onOpenChange} />);

    fireEvent.click(screen.getByRole('button', { name: /Cancel/ }));
    expect(onOpenChange).toHaveBeenCalledWith(false);
  });

  it('disables submit button while submitting', async () => {
    apiClient.bookApi.createReview.mockImplementation(
      () => new Promise((resolve) => setTimeout(resolve, 1000))
    );

    render(<ReviewSubmissionDialog {...defaultProps} />);

    const stars = screen.getAllByRole('radio');
    fireEvent.click(stars[0]);
    fireEvent.change(screen.getByPlaceholderText(/Share your thoughts/), {
      target: { value: 'Test' },
    });
    fireEvent.click(screen.getByRole('button', { name: /Submit Review/ }));

    await waitFor(() => {
      expect(screen.getByRole('button', { name: /Submitting/ })).toBeDisabled();
    });
  });

  // Edit mode tests
  const existingReview = {
    id: 'review-789',
    rating: 4,
    comment: 'Original review text',
    orderItemId: 'item-456',
  };

  it('renders edit mode dialog with existing review data', () => {
    render(<ReviewSubmissionDialog {...defaultProps} existingReview={existingReview} />);
    expect(screen.getByText('Edit Your Review')).toBeInTheDocument();
    expect(screen.getByText(/Editing:/)).toBeInTheDocument();
  });

  it('pre-fills rating and comment in edit mode', () => {
    render(<ReviewSubmissionDialog {...defaultProps} existingReview={existingReview} />);
    const stars = screen.getAllByRole('radio');
    const filledStars = stars.filter((star) =>
      star.querySelector('svg')?.classList.contains('text-amber-400')
    );
    expect(filledStars).toHaveLength(4);
    expect(screen.getByPlaceholderText(/Share your thoughts/)).toHaveValue('Original review text');
  });

  it('calls userApi.updateMyReview with correct payload on edit submit', async () => {
    apiClient.userApi.updateMyReview.mockResolvedValue({ data: { id: 'review-789' } });

    render(<ReviewSubmissionDialog {...defaultProps} existingReview={existingReview} />);

    // Click 5th star to change rating
    const stars = screen.getAllByRole('radio');
    fireEvent.click(stars[4]);

    // Change comment
    const textarea = screen.getByPlaceholderText(/Share your thoughts/);
    fireEvent.change(textarea, { target: { value: 'Updated review text' } });

    // Submit
    fireEvent.click(screen.getByRole('button', { name: /Save Changes/ }));

    await waitFor(() => {
      expect(apiClient.userApi.updateMyReview).toHaveBeenCalledWith({
        reviewId: 'review-789',
        updateMyReviewRequest: {
          rating: 5,
          comment: 'Updated review text',
        },
      });
    });
  });
});
