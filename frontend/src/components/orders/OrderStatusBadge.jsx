import React from 'react';

import { cn } from '@/lib/utils';

const statusConfig = {
  pending: { label: 'Pending', className: 'bg-gray-100 text-gray-700' },
  paid: { label: 'Paid', className: 'bg-blue-100 text-blue-700' },
  shipped: { label: 'Shipped', className: 'bg-purple-100 text-purple-700' },
  delivered: { label: 'Delivered', className: 'bg-green-100 text-green-700' },
  cancelled: { label: 'Cancelled', className: 'bg-red-100 text-red-700' },
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
