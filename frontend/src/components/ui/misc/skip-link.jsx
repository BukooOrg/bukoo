import { SkipForward } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

export function SkipLink({
  className,
  href = '#main-content',
  children = 'Skip to main content',
  ...props
}) {
  return (
    <a
      href={href}
      className={cn(
        'absolute left-4 top-4 -translate-y-20 z-[9999]',
        'px-4 py-3 rounded-lg bg-primary text-primary-foreground font-medium text-sm',
        'focus:translate-y-0 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2',
        'transition-transform duration-200 ease-out',
        className
      )}
      {...props}>
      <span className='flex items-center gap-2'>
        <SkipForward className='w-4 h-4' />
        {children}
      </span>
    </a>
  );
}
