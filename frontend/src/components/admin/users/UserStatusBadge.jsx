import React from 'react';

import { Badge } from '@/components/ui/data-display/badge';
import { cn } from '@/lib/utils';

export function RoleBadge({ role }) {
  const isAdmin = role === 'admin';
  return (
    <Badge
      variant={isAdmin ? 'default' : 'outline'}
      className={cn(
        'text-[10px] font-black uppercase tracking-widest',
        isAdmin
          ? 'bg-primary/10 text-primary border-primary/20'
          : 'bg-primary/5 text-primary/40 border-primary/10'
      )}>
      {isAdmin ? 'Admin' : 'User'}
    </Badge>
  );
}

export function StatusBadge({ status }) {
  const statusMap = {
    pending: {
      label: 'Pending',
      bg: 'bg-amber-500/10',
      text: 'text-amber-700',
      border: 'border-amber-500/20',
    },
    active: {
      label: 'Active',
      bg: 'bg-green-500/10',
      text: 'text-green-700',
      border: 'border-green-500/20',
    },
    suspended: {
      label: 'Suspended',
      bg: 'bg-destructive/10',
      text: 'text-destructive',
      border: 'border-destructive/20',
    },
  };

  const config = statusMap[status] || statusMap.pending;

  return (
    <Badge
      variant='outline'
      className={cn(
        'text-[10px] font-black uppercase tracking-widest',
        config.bg,
        config.text,
        config.border
      )}>
      {config.label}
    </Badge>
  );
}
