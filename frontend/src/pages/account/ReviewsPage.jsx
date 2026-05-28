import { Star } from 'lucide-react';
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { ReviewCard, ReviewForm } from '@/components/reviews';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/overlays/dialog';
import { userApi } from '@/lib/apiClient';

export default function AccountReviewsPage() {
  const [reviews, setReviews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [hasLoadedOnce, setHasLoadedOnce] = useState(false);

  // Edit state
  const [editingReview, setEditingReview] = useState(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  // Delete state
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    async function loadReviews() {
      setLoading(true);
      try {
        const response = await userApi.findMyReviews({ page, pageSize: 10 });
        const data = response.data;
        setReviews(data.items || []);
        setTotalPages(data.meta?.totalPages || 1);
        if (data.items?.length > 0) {
          setHasLoadedOnce(true);
        }
      } catch {
        setReviews([]);
      } finally {
        setLoading(false);
      }
    }
    loadReviews();
  }, [page]);

  const handleEdit = (review) => {
    setEditingReview(review);
    setEditDialogOpen(true);
  };

  const handleSaveEdit = async (formData) => {
    if (!editingReview) return;
    setSaving(true);
    try {
      await userApi.updateMyReview({
        reviewId: editingReview.id,
        updateMyReviewRequest: {
          rating: formData.rating,
          comment: formData.comment,
        },
      });
      toast.success('Review updated');
      setEditDialogOpen(false);
      setEditingReview(null);
      // Refresh list
      const response = await userApi.findMyReviews({ page, pageSize: 10 });
      setReviews(response.data.items || []);
    } catch (error) {
      toast.error(`Failed to update review: ${error.message || 'Unknown error'}`);
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (reviewId) => {
    setDeletingId(reviewId);
    try {
      await userApi.softDeleteMyReview({ reviewId });
      toast.success('Review deleted');
      setReviews((prev) => prev.filter((r) => r.id !== reviewId));
    } catch (error) {
      toast.error(`Failed to delete review: ${error.message || 'Unknown error'}`);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  const showEmptyState = !reviews.length && !hasLoadedOnce;

  if (showEmptyState) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <div className='flex justify-center mb-4'>
            <Star className='w-12 h-12 text-primary/20' />
          </div>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            No Reviews Yet
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-2'>
            Share your thoughts on books you've purchased and received.
          </p>
          <Link to='/shop'>
            <Button className='mt-10 bg-primary text-secondary h-14 text-lg' size='lg'>
              Browse Books
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className='px-sides py-16'>
      <div className='max-w-4xl mx-auto'>
        <div className='mb-8'>
          <h1 className='font-serif text-4xl font-black tracking-tighter text-primary'>
            My Reviews
          </h1>
          <p className='text-primary/40 font-bold italic text-sm mt-1'>
            Manage your book reviews and ratings
          </p>
        </div>

        {!reviews.length ? (
          <div className='text-center py-24'>
            <p className='font-serif text-2xl italic text-primary/40'>No reviews found.</p>
          </div>
        ) : (
          <div className='space-y-4'>
            {reviews.map((review) => (
              <ReviewCard
                key={review.id}
                review={review}
                onEdit={() => handleEdit(review)}
                onDelete={deletingId === review.id ? undefined : () => handleDelete(review.id)}
              />
            ))}
          </div>
        )}

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
      </div>

      {/* Edit dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Review</DialogTitle>
          </DialogHeader>
          {editingReview && (
            <ReviewForm
              review={editingReview}
              onSubmit={handleSaveEdit}
              onCancel={() => {
                setEditDialogOpen(false);
                setEditingReview(null);
              }}
              loading={saving}
            />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
