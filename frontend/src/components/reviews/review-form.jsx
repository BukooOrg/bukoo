import { zodResolver } from '@hookform/resolvers/zod';
import { X } from 'lucide-react';
import React from 'react';
import { useForm } from 'react-hook-form';
import { z } from 'zod';

import { StarRating } from '@/components/reviews/star-rating';
import { Button } from '@/components/ui/forms/button';
import { Field } from '@/components/ui/forms/field';
import { cn } from '@/lib/utils';

const reviewSchema = z.object({
  rating: z.number().min(1, 'Please select a rating').max(5),
  comment: z
    .string()
    .min(1, 'Please write a comment')
    .max(2000, 'Comment is too long (max 2000 characters)'),
});

export function ReviewForm({ review, onSubmit, onCancel, loading = false, className }) {
  const isEditing = !!review;

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(reviewSchema),
    defaultValues: {
      rating: review?.rating || 0,
      comment: review?.comment || '',
    },
  });

  const currentRating = watch('rating');

  const handleFormSubmit = handleSubmit((data) => {
    onSubmit(data);
  });

  return (
    <form onSubmit={handleFormSubmit} className={cn('space-y-6', className)} noValidate>
      {/* Rating */}
      <Field label='Rating' error={errors.rating?.message} required>
        <StarRating
          value={currentRating}
          size='lg'
          interactive
          onChange={(val) => setValue('rating', val, { shouldValidate: true })}
        />
      </Field>

      {/* Comment */}
      <Field label='Your Review' error={errors.comment?.message} required>
        <textarea
          {...register('comment')}
          rows={4}
          className='w-full px-3 py-2 text-sm border rounded-lg border-primary/10 focus:border-primary/30 focus:outline-none focus:ring-2 focus:ring-primary/10 transition-all resize-none'
          placeholder='Share your thoughts about this book...'
        />
        <p className='mt-1 text-xs text-primary/30'>{watch('comment').length}/2000 characters</p>
      </Field>

      {/* Actions */}
      <div className='flex items-center justify-end gap-3'>
        {onCancel && (
          <Button
            type='button'
            variant='outline'
            onClick={onCancel}
            disabled={loading}
            className='h-10'>
            <X className='w-4 h-4 mr-1.5' />
            Cancel
          </Button>
        )}
        <Button
          type='submit'
          disabled={loading || currentRating === 0}
          className='h-10 bg-primary text-white hover:bg-primary/90'>
          {loading
            ? isEditing
              ? 'Saving...'
              : 'Submitting...'
            : isEditing
              ? 'Save Changes'
              : 'Submit Review'}
        </Button>
      </div>
    </form>
  );
}
