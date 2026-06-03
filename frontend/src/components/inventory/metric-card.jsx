import { cn } from '@/lib/utils';

const accentMap = {
  default: 'border-primary/10 bg-primary/[0.03]',
  red: 'border-destructive/20 bg-destructive/[0.04]',
  amber: 'border-primary/20 bg-primary/[0.04]',
  green: 'border-primary/20 bg-primary/[0.04]',
};

const iconBgMap = {
  default: 'bg-primary/10 text-primary',
  red: 'bg-destructive/10 text-destructive',
  amber: 'bg-primary/10 text-primary',
  green: 'bg-primary/10 text-primary',
};

export function MetricCard({ icon: Icon, label, value, accent = 'default', className }) {
  return (
    <div
      className={cn(
        'rounded-2xl border p-5 flex items-start gap-4 transition-colors',
        accentMap[accent],
        className
      )}>
      <div className={cn('rounded-2xl p-2.5 shrink-0', iconBgMap[accent])}>
        <Icon className='w-5 h-5' />
      </div>
      <div className='space-y-1 min-w-0'>
        <p className='text-xs font-bold uppercase tracking-widest text-primary/40'>{label}</p>
        <p className='font-serif text-3xl font-black tracking-tight text-primary truncate'>
          {value}
        </p>
      </div>
    </div>
  );
}
