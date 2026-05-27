import { Check, EyeOff, MoreVertical, Pencil, Trash2 } from 'lucide-react';
import React, { useState } from 'react';
import { Link } from 'react-router-dom';

import { StarRating } from '@/components/reviews/star-rating';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/overlays/dropdown-menu';
import { cn } from '@/lib/utils';

function formatDate(date) {
  return new Date(date).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

export function ReviewCard({
  review,
  variant = 'default',
  isOwn = false,
  onEdit,
  onDelete,
  onHideRestore,
  className,
}) {
  const [open, setOpen] = useState(false);

  const isHidden = review.isHidden;

  return (
    <div
      className={cn(
        'p-4 border rounded-xl bg-white transition-colors',
        isHidden && 'opacity-60',
        variant === 'compact' ? 'border-primary/5' : 'border-primary/10 hover:border-primary/20',
        className
      )}>
      <div className='flex items-start justify-between gap-3'>
        <div className='flex-1 min-w-0'>
          {/* Header: rating + date */}
          <div className='flex items-center gap-3 mb-2'>
            <StarRating value={review.rating} size='sm' />
            <span className='text-xs text-primary/30'>{formatDate(review.createdAt)}</span>
            {isOwn && (
              <span className='flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-primary/10 text-primary'>
                <Check className='w-3 h-3' />
                Your Review
              </span>
            )}
            {isHidden && (
              <span className='flex items-center gap-1 px-2 py-0.5 text-xs rounded-full bg-red-50 text-red-600'>
                <EyeOff className='w-3 h-3' />
                Hidden
              </span>
            )}
          </div>

          {/* Book info (shown in admin/account views) */}
          {review.book && (
            <Link
              to={
                variant === 'admin'
                  ? `/admin/books/${review.book.id}`
                  : `/product/${review.book.id}`
              }
              className='text-sm font-medium transition-colors text-primary hover:text-primary/70'>
              {review.book.title}
            </Link>
          )}

          {/* Comment */}
          {review.comment && (
            <p className='mt-2 text-sm leading-relaxed text-primary/70'>{review.comment}</p>
          )}

          {/* Updated indicator */}
          {review.updatedAt && review.updatedAt !== review.createdAt && (
            <p className='mt-1 text-xs italic text-primary/30'>(edited)</p>
          )}
        </div>

        {/* Actions menu */}
        {(onEdit || onDelete || onHideRestore) && (
          <DropdownMenu open={open} onOpenChange={setOpen}>
            <DropdownMenuTrigger asChild>
              <button
                className='p-1 rounded-lg hover:bg-primary/5 transition-colors shrink-0'
                aria-label='Review actions'>
                <MoreVertical className='w-4 h-4 text-primary/40' />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align='end'>
              {onEdit && (
                <DropdownMenuItem onClick={onEdit}>
                  <Pencil className='w-4 h-4 mr-2' />
                  Edit
                </DropdownMenuItem>
              )}
              {onHideRestore && (
                <DropdownMenuItem onClick={onHideRestore}>
                  <EyeOff className='w-4 h-4 mr-2' />
                  {isHidden ? 'Restore' : 'Hide'}
                </DropdownMenuItem>
              )}
              {onDelete && (
                <DropdownMenuItem onClick={onDelete} className='text-red-600 focus:text-red-600'>
                  <Trash2 className='w-4 h-4 mr-2' />
                  Delete
                </DropdownMenuItem>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </div>
  );
}
