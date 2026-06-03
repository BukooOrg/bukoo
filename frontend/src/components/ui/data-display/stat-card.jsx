import { cva } from 'class-variance-authority';
import React from 'react';
import { Link } from 'react-router-dom';

import { cn } from '@/lib/utils';

const statCardVariants = cva(
  'rounded-2xl border bg-card p-6 transition-all duration-200 hover:shadow-md',
  {
    variants: {
      variant: {
        default: 'border-border',
        accent: 'border-primary/20 bg-primary/5',
        success: 'border-primary/20 bg-primary/10',
        warning: 'border-primary/10 bg-primary/5',
        destructive: 'border-destructive/20 bg-destructive/10',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
);

export function StatCard({
  className,
  variant,
  icon: Icon,
  iconClassName,
  label,
  value,
  trend,
  trendLabel,
  href,
  ...props
}) {
  const content = (
    <div className={cn(statCardVariants({ variant, className }))} {...props}>
      <div className='flex items-start justify-between'>
        <div className='space-y-2 flex-1 min-w-0'>
          <p className='text-sm font-medium text-muted-foreground'>{label}</p>
          <p className='font-serif text-3xl font-bold text-primary tabular-nums'>{value}</p>

          {trend !== undefined && (
            <div className='flex items-center gap-1.5'>
              <TrendIndicator value={trend} />
              {trendLabel && <span className='text-xs text-muted-foreground'>{trendLabel}</span>}
            </div>
          )}
        </div>

        {Icon && (
          <div className={cn('p-3 rounded-lg bg-muted text-muted-foreground', iconClassName)}>
            <Icon className='w-5 h-5' />
          </div>
        )}
      </div>
    </div>
  );

  if (href) {
    return (
      <Link to={href} className='block cursor-pointer'>
        {content}
      </Link>
    );
  }

  return content;
}

function TrendIndicator({ value }) {
  if (value === 0) return null;

  const isPositive = value > 0;
  const color = isPositive ? 'text-primary' : 'text-destructive';

  return (
    <span className={cn('text-xs font-semibold tabular-nums', color)}>
      {isPositive ? '↑' : '↓'} {Math.abs(value)}%
    </span>
  );
}

export function StatCardGrid({ className, children, ...props }) {
  return (
    <div
      className={cn('grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4', className)}
      {...props}>
      {children}
    </div>
  );
}
