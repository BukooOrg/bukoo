import { CheckCircle2, Clock, Loader2, XCircle } from 'lucide-react';

import { Badge } from '@/components/ui/data-display/badge';
import { Spinner } from '@/components/ui/feedback/spinner';
import { cn } from '@/lib/utils';

const statusConfig = {
  pending: {
    label: 'Pending',
    className: 'bg-gray-100 text-gray-700 border-gray-200',
    icon: Clock,
  },
  processing: {
    label: 'Processing',
    className: 'bg-blue-100 text-blue-700 border-blue-200',
    icon: Loader2,
  },
  completed: {
    label: 'Completed',
    className: 'bg-green-100 text-green-700 border-green-200',
    icon: CheckCircle2,
  },
  failed: {
    label: 'Failed',
    className: 'bg-red-100 text-red-700 border-red-200',
    icon: XCircle,
  },
};

export function ReportStatusBadge({ status, className }) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  return (
    <Badge variant='outline' className={cn(config.className, 'gap-1.5', className)}>
      {status === 'processing' ? (
        <Spinner size='sm' className='text-blue-600' />
      ) : (
        <Icon className='size-3' />
      )}
      {config.label}
    </Badge>
  );
}
