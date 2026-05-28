import { cn } from '@/lib/utils';

const statusConfig = {
  active: { label: 'Active', color: 'bg-primary/10 text-primary' },
  pending: { label: 'Pending', color: 'bg-yellow-100 text-yellow-800' },
  suspended: { label: 'Suspended', color: 'bg-destructive/10 text-red-800' },
};

export function StatusBadge({ status = 'pending', className }) {
  const config = statusConfig[status] || statusConfig.pending;
  return (
    <span
      className={cn(
        'inline-flex px-2.5 py-0.5 rounded-full text-xs font-bold',
        config.color,
        className
      )}>
      {config.label}
    </span>
  );
}
