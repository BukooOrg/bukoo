import { cn } from '@/lib/utils';

const statusConfig = {
  active: { label: 'Active', color: 'bg-primary/10 text-primary' },
  pending: { label: 'Pending', color: 'bg-primary/5 text-muted-foreground' },
  suspended: { label: 'Suspended', color: 'bg-destructive/10 text-destructive' },
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
