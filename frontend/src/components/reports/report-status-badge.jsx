import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/data-display/badge';
import { Spinner } from '@/components/ui/feedback/spinner';
import { cn } from '@/lib/utils';

const statusConfig = {
  pending: {
    label: 'Pending',
    className: 'bg-primary/5 text-primary border-primary/5',
    icon: Clock,
  },
  processing: {
    label: 'Processing',
    className: 'bg-primary/10 text-primary border-primary/20',
    icon: Loader2,
  },
  completed: {
    label: 'Completed',
    className: 'bg-primary/10 text-primary border-primary/10',
    icon: CheckCircle2,
  },
  failed: {
    label: 'Failed',
    className: 'bg-destructive/10 text-destructive border-destructive/30',
    icon: XCircle,
  },
};

export function ReportStatusBadge({ status, className }) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <Badge variant='outline' className={cn(config.className, 'gap-1.5', className)}>
      {status === 'processing' ? (
        <Spinner size='sm' className='text-primary' />
      ) : (
        <Icon className='size-3' />
      )}
      {config.label}
    </Badge>
  );
}
