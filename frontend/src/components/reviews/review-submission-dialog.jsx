import { BookOpen } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'sonner';

import { ReviewForm } from '@/components/reviews';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from '@/components/ui/overlays/dialog';
import { bookApi, userApi } from '@/lib/apiClient';

export function ReviewSubmissionDialog({
  bookId,
  orderItemId,
  bookTitle,
  existingReview,
  open,
  onOpenChange,
  onSubmitted,
}) {
  const [submitting, setSubmitting] = useState(false);

  const isEditing = !!existingReview;

  const handleSubmit = async (formData) => {
    setSubmitting(true);
    try {
      if (isEditing) {
        await userApi.updateMyReview({
          reviewId: existingReview.id,
          updateMyReviewRequest: {
            rating: formData.rating,
            comment: formData.comment,
          },
        });
        toast.success('Review updated successfully!');
      } else {
        await bookApi.createReview({
          bookId,
          createReviewRequest: {
            orderItemId,
            rating: formData.rating,
            comment: formData.comment,
          },
        });
        toast.success('Review submitted successfully!');
      }
      onOpenChange(false);
      onSubmitted?.();
    } catch (error) {
      const message = error?.body?.error?.message || error?.message;
      if (message?.toLowerCase().includes('already')) {
        toast.error('You have already reviewed this item.');
      } else if (
        message?.toLowerCase().includes('not eligible') ||
        message?.toLowerCase().includes('eligibility')
      ) {
        toast.error('This item is not eligible for review.');
      } else {
        toast.error('Failed to submit review. Please try again.');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className='sm:max-w-md'>
        <DialogHeader>
          <DialogTitle className='flex items-center gap-2'>
            <BookOpen className='w-5 h-5 text-primary/60' />
            {isEditing ? 'Edit Your Review' : 'Write a Review'}
          </DialogTitle>
          <DialogDescription className='sr-only'>
            {isEditing ? 'Edit your review for' : 'Submit a review for'} {bookTitle}
          </DialogDescription>
          <p className='text-sm text-primary/40 mt-1'>
            {isEditing ? 'Editing:' : 'Reviewing:'}{' '}
            <span className='font-medium text-primary/70'>{bookTitle}</span>
          </p>
        </DialogHeader>
        <ReviewForm
          review={
            isEditing ? { rating: existingReview.rating, comment: existingReview.comment } : null
          }
          onSubmit={handleSubmit}
          onCancel={() => onOpenChange(false)}
          loading={submitting}
        />
      </DialogContent>
    </Dialog>
  );
}
