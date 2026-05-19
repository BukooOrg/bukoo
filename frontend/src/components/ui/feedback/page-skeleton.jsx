import React from 'react';

import { Skeleton } from '@/components/ui/feedback/skeleton';
import { cn } from '@/lib/utils';

export function PageSkeleton({
  className,
  lines = 3,
  showHeader = true,
  showFilters = true,
  ...props
}) {
  return (
    <div className={cn('space-y-6', className)} {...props}>
      {showHeader && (
        <div className='space-y-2'>
          <Skeleton className='h-8 w-48' />
          <Skeleton className='h-4 w-72' />
        </div>
      )}

      {showFilters && (
        <div className='flex gap-3 flex-wrap'>
          <Skeleton className='h-9 w-32' />
          <Skeleton className='h-9 w-40' />
          <Skeleton className='h-9 w-24' />
          <Skeleton className='h-9 flex-1 min-w-48' />
        </div>
      )}

      <div className='space-y-3'>
        {Array.from({ length: lines }).map((_, i) => (
          <Skeleton key={i} className='h-16 w-full' />
        ))}
      </div>
    </div>
  );
}

export function CardSkeleton({ className, ...props }) {
  return (
    <div className={cn('rounded-xl border p-6 space-y-4', className)} {...props}>
      <Skeleton className='h-6 w-3/4' />
      <Skeleton className='h-4 w-full' />
      <Skeleton className='h-4 w-2/3' />
      <div className='flex gap-2 pt-2'>
        <Skeleton className='h-8 w-20' />
        <Skeleton className='h-8 w-20' />
      </div>
    </div>
  );
}

export function DetailSkeleton({ className, sections = 2, ...props }) {
  return (
    <div className={cn('space-y-8', className)} {...props}>
      <div className='space-y-3'>
        <Skeleton className='h-10 w-64' />
        <Skeleton className='h-5 w-96' />
      </div>

      {Array.from({ length: sections }).map((_, i) => (
        <div key={i} className='rounded-xl border p-6 space-y-4'>
          <Skeleton className='h-6 w-40' />
          <div className='grid grid-cols-2 gap-4'>
            <div className='space-y-2'>
              <Skeleton className='h-4 w-24' />
              <Skeleton className='h-5 w-full' />
            </div>
            <div className='space-y-2'>
              <Skeleton className='h-4 w-24' />
              <Skeleton className='h-5 w-full' />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export function TableSkeleton({ className, rows = 5, ...props }) {
  return (
    <div className={cn('rounded-xl border overflow-hidden', className)} {...props}>
      <div className='border-b bg-muted/50'>
        <div className='grid grid-cols-6 gap-4 px-6 py-3'>
          {Array.from({ length: 6 }).map((_, i) => (
            <Skeleton key={i} className='h-4 w-full' />
          ))}
        </div>
      </div>
      <div>
        {Array.from({ length: rows }).map((_, i) => (
          <div key={i} className='grid grid-cols-6 gap-4 px-6 py-4 border-b last:border-b-0'>
            {Array.from({ length: 6 }).map((_, j) => (
              <Skeleton key={j} className='h-4 w-full' />
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
