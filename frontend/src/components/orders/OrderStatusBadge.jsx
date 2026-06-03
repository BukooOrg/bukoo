import React from 'react';

import { cn } from '@/lib/utils';

const statusConfig = {
  pending: { label: 'Pending', className: 'bg-primary/5 text-primary' },
  paid: { label: 'Paid', className: 'bg-primary/10 text-primary' },
  shipped: { label: 'Shipped', className: 'bg-primary/10 text-primary' },
  delivered: { label: 'Delivered', className: 'bg-primary/10 text-primary' },
  cancelled: { label: 'Cancelled', className: 'bg-destructive/10 text-destructive' },
};

export function OrderStatusBadge({ status, className }) {
  const config = statusConfig[status?.toLowerCase()] || statusConfig.pending;

  return (
    <span
      className={cn(
        'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
        config.className,
        className
      )}>
      {config.label}
    </span>
  );
}
