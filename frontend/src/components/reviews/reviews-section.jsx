import { MessageSquare } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { toast } from 'sonner';

import { ReviewCard, ReviewSubmissionDialog, StarRating } from '@/components/reviews';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { useAuth } from '@/context/AuthContext';
import { bookApi, orderApi, userApi } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

export function ReviewsSection({ bookId, className }) {
  const { user } = useAuth();
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const [averageRating, setAverageRating] = useState(0);

  // Review submission state
  const [submitDialogOpen, setSubmitDialogOpen] = useState(false);
  const [eligibleItem, setEligibleItem] = useState(null);
  const [fetchingEligible, setFetchingEligible] = useState(false);

  // Existing review state (for edit mode)
  const [myReview, setMyReview] = useState(null);
  const [checkingExisting, setCheckingExisting] = useState(false);

  useEffect(() => {
    async function loadReviews() {
      setLoading(true);
      try {
        const response = await bookApi.findReviews({ bookId, page, pageSize: 5 });
        const data = response.data;
        setReviews(data.items || []);
        setTotalPages(data.meta?.totalPages || 1);
        setTotalCount(data.meta?.totalCount || 0);

        // Calculate average
        if (data.items?.length > 0) {
          const sum = data.items.reduce((acc, r) => acc + r.rating, 0);
          setAverageRating(sum / data.items.length);
        }
      } catch {
        setReviews([]);
      } finally {
        setLoading(false);
      }
    }
    loadReviews();
  }, [bookId, page]);

  // Check if user already has a review for this book
  useEffect(() => {
    if (!user) return;

    async function checkExistingReview() {
      setCheckingExisting(true);
      try {
        const response = await userApi.findMyReviews({ page: 1, pageSize: 50 });
        const myReviews = response.data.items || [];
        const existing = myReviews.find((r) => r.bookId === bookId);
        setMyReview(existing || null);
      } catch {
        // Silently fail — user can still attempt to write a review
      } finally {
        setCheckingExisting(false);
      }
    }
    checkExistingReview();
  }, [user, bookId]);

  const handleWriteReview = async () => {
    setFetchingEligible(true);
    try {
      // Fetch all orders and filter for delivered ones client-side
      const ordersResponse = await orderApi.findOrders({
        page: 1,
        pageSize: 50,
      });
      const allOrders = ordersResponse.data.items || [];
      const deliveredOrders = allOrders.filter((o) => o.status === 'delivered');

      if (deliveredOrders.length === 0) {
        toast.info('You need to have a delivered order to write a review.');
        return;
      }

      // Find an order item for this book in any delivered order
      let found = null;
      for (const order of deliveredOrders) {
        try {
          const detail = await orderApi.viewOrderDetail({ orderId: order.id });
          const matchingItem = detail.data.items?.find((item) => item.bookId === bookId);
          if (matchingItem) {
            found = matchingItem;
            break;
          }
        } catch {
          // Skip orders we can't fetch details for
        }
      }

      if (!found) {
        toast.info(
          'No delivered order found for this book. You can only review books you have received.'
        );
        return;
      }

      setEligibleItem(found);
      setSubmitDialogOpen(true);
    } catch {
      toast.error('Failed to check review eligibility. Please try again.');
    } finally {
      setFetchingEligible(false);
    }
  };

  const handleEditReview = () => {
    setSubmitDialogOpen(true);
  };

  const handleDeleteReview = async () => {
    if (!myReview) return;
    try {
      await userApi.softDeleteMyReview({ reviewId: myReview.id });
      toast.success('Review deleted.');
      setMyReview(null);
      await refreshReviews();
    } catch {
      toast.error('Failed to delete review.');
    }
  };

  const refreshReviews = async () => {
    try {
      const [reviewsRes, myReviewsRes] = await Promise.all([
        bookApi.findReviews({ bookId, page, pageSize: 5 }),
        user ? userApi.findMyReviews({ page: 1, pageSize: 50 }) : Promise.resolve(null),
      ]);

      const reviewsData = reviewsRes.data;
      setReviews(reviewsData.items || []);
      setTotalPages(reviewsData.meta?.totalPages || 1);
      setTotalCount(reviewsData.meta?.totalCount || 0);

      if (reviewsData.items?.length > 0) {
        const sum = reviewsData.items.reduce((acc, r) => acc + r.rating, 0);
        setAverageRating(sum / reviewsData.items.length);
      } else {
        setAverageRating(0);
      }

      if (myReviewsRes) {
        const myReviews = myReviewsRes.data.items || [];
        const existing = myReviews.find((r) => r.bookId === bookId);
        setMyReview(existing || null);
      }
    } catch {
      // Silently fail — user can still see the old data
    }
  };

  const handleReviewSubmitted = async () => {
    setSubmitDialogOpen(false);
    setEligibleItem(null);
    await refreshReviews();
  };

  const isOwnReview = (review) => user?.id && review.userId === user.id;

  if (loading) {
    return (
      <div className='flex items-center justify-center py-12'>
        <Spinner size='lg' />
      </div>
    );
  }

  return (
    <div className={cn('mt-16 pt-12 border-t border-primary/10', className)}>
      {/* Section header */}
      <div className='flex items-center justify-between mb-8'>
        <div>
          <div className='flex items-center gap-3 mb-2'>
            <h2 className='text-2xl font-serif font-bold text-primary'>Customer Reviews</h2>
            <span className='text-sm text-primary/40'>({totalCount})</span>
          </div>
          {totalCount > 0 && (
            <div className='flex items-center gap-2'>
              <StarRating value={Math.round(averageRating)} size='md' />
              <span className='text-sm text-primary/60'>{averageRating.toFixed(1)} average</span>
            </div>
          )}
        </div>

        {/* Write/Edit review button — customers only, admins can only view */}
        {user && user.role !== 'admin' && (
          <Button
            onClick={myReview ? handleEditReview : handleWriteReview}
            disabled={fetchingEligible || checkingExisting}
            className='h-10 bg-primary text-white hover:bg-primary/90'>
            <MessageSquare className='w-4 h-4 mr-1.5' />
            {checkingExisting
              ? 'Checking...'
              : myReview
                ? 'Edit Your Review'
                : fetchingEligible
                  ? 'Checking...'
                  : 'Write a Review'}
          </Button>
        )}
      </div>

      {/* Reviews list */}
      {reviews.length === 0 ? (
        <div className='py-16 text-center'>
          <MessageSquare className='w-10 h-10 mx-auto mb-4 text-primary/20' />
          <p className='font-serif text-xl italic text-primary/30'>
            No reviews yet. Be the first to share your thoughts!
          </p>
        </div>
      ) : (
        <div className='space-y-4'>
          {reviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              variant='compact'
              isOwn={isOwnReview(review)}
              onEdit={isOwnReview(review) ? handleEditReview : undefined}
              onDelete={isOwnReview(review) ? handleDeleteReview : undefined}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='flex items-center justify-center gap-3 mt-8'>
          <Button
            variant='outline'
            disabled={page <= 1}
            onClick={() => setPage((p) => p - 1)}
            className='h-10'>
            Previous
          </Button>
          <span className='text-sm text-primary/40'>
            Page {page} of {totalPages}
          </span>
          <Button
            variant='outline'
            disabled={page >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className='h-10'>
            Next
          </Button>
        </div>
      )}

      {/* Review submission dialog */}
      <ReviewSubmissionDialog
        bookId={bookId}
        orderItemId={eligibleItem?.id || myReview?.orderItemId}
        bookTitle={eligibleItem?.bookTitle || myReview?.book?.title}
        existingReview={myReview}
        open={submitDialogOpen}
        onOpenChange={(open) => {
          setSubmitDialogOpen(open);
          if (!open) setEligibleItem(null);
        }}
        onSubmitted={handleReviewSubmitted}
      />
    </div>
  );
}
