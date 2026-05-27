import { Star } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

export function StarRating({ value = 0, size = 'md', interactive = false, onChange, className }) {
  const sizeClasses = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
    xl: 'w-6 h-6',
  };

  const starSize = sizeClasses[size] || sizeClasses.md;

  return (
    <div
      className={cn('flex items-center gap-0.5', className)}
      role={interactive ? 'radiogroup' : undefined}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type='button'
          disabled={!interactive}
          onClick={() => interactive && onChange?.(star)}
          onKeyDown={(e) => {
            if (interactive && (e.key === 'Enter' || e.key === ' ')) {
              e.preventDefault();
              onChange?.(star);
            }
          }}
          className={cn(
            'p-0.5 transition-colors',
            interactive &&
              'cursor-pointer hover:scale-110 focus:outline-none focus-visible:ring-2 focus-visible:ring-primary rounded'
          )}
          role={interactive ? 'radio' : undefined}
          aria-checked={interactive ? star === value : undefined}
          aria-label={`${star} star${star > 1 ? 's' : ''}`}
          tabIndex={interactive ? 0 : -1}>
          <Star
            className={cn(
              starSize,
              star <= value ? 'fill-amber-400 text-amber-400' : 'fill-transparent text-gray-300'
            )}
          />
        </button>
      ))}
    </div>
  );
}
