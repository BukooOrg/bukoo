import { cn } from '@/lib/utils';

const accentMap = {
  default: 'border-primary/10 bg-primary/[0.03]',
  red: 'border-red-500/20 bg-red-500/[0.04]',
  amber: 'border-amber-500/20 bg-amber-500/[0.04]',
  green: 'border-green-500/20 bg-green-500/[0.04]',
};

const iconBgMap = {
  default: 'bg-primary/10 text-primary',
  red: 'bg-red-500/10 text-red-600',
  amber: 'bg-amber-500/10 text-amber-600',
  green: 'bg-green-500/10 text-green-600',
};

export function MetricCard({ icon: Icon, label, value, accent = 'default', className }) {
  return (
    <div
      className={cn(
        'rounded-xl border p-5 flex items-start gap-4 transition-colors',
        accentMap[accent],
        className
      )}>
      <div className={cn('rounded-lg p-2.5 shrink-0', iconBgMap[accent])}>
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
