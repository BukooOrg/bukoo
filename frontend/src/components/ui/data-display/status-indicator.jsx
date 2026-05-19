import { Check, Clock, Package, Truck, XCircle } from 'lucide-react';
import React from 'react';

import { cn } from '@/lib/utils';

const statusConfig = {
  pending: {
    label: 'Pending',
    icon: Clock,
    color: 'text-amber-600',
    bg: 'bg-amber-50',
    border: 'border-amber-200',
  },
  processing: {
    label: 'Processing',
    icon: Package,
    color: 'text-blue-600',
    bg: 'bg-blue-50',
    border: 'border-blue-200',
  },
  shipped: {
    label: 'Shipped',
    icon: Truck,
    color: 'text-indigo-600',
    bg: 'bg-indigo-50',
    border: 'border-indigo-200',
  },
  delivered: {
    label: 'Delivered',
    icon: Check,
    color: 'text-green-600',
    bg: 'bg-green-50',
    border: 'border-green-200',
  },
  cancelled: {
    label: 'Cancelled',
    icon: XCircle,
    color: 'text-red-600',
    bg: 'bg-red-50',
    border: 'border-red-200',
  },
  refunded: {
    label: 'Refunded',
    icon: XCircle,
    color: 'text-gray-600',
    bg: 'bg-gray-50',
    border: 'border-gray-200',
  },
};

export function StatusBadge({ status, className, size = 'default', ...props }) {
  const config = statusConfig[status] || statusConfig.pending;
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs gap-1',
    default: 'px-2.5 py-1 text-sm gap-1.5',
    lg: 'px-3 py-1.5 text-base gap-2',
  };

  const iconSizes = {
    sm: 'w-3 h-3',
    default: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full border',
        config.bg,
        config.border,
        config.color,
        sizeClasses[size],
        className
      )}
      {...props}>
      <Icon className={cn(iconSizes[size], 'shrink-0')} />
      {config.label}
    </span>
  );
}

export function StatusTimeline({ steps, currentStep, className, ...props }) {
  const stepKeys = ['pending', 'processing', 'shipped', 'delivered'];
  const currentIndex = stepKeys.indexOf(currentStep);

  const defaultSteps = [
    { key: 'pending', label: 'Placed' },
    { key: 'processing', label: 'Processing' },
    { key: 'shipped', label: 'Shipped' },
    { key: 'delivered', label: 'Delivered' },
  ];

  const displaySteps = steps || defaultSteps;

  return (
    <div className={cn('w-full', className)} {...props}>
      <div className='relative'>
        <div className='absolute top-4 left-0 right-0 h-0.5 bg-muted' />
        <div
          className='absolute top-4 left-0 h-0.5 bg-primary transition-all duration-500'
          style={{
            width: `${(currentIndex / (displaySteps.length - 1)) * 100}%`,
          }}
        />

        <div className='relative flex justify-between'>
          {displaySteps.map((step, index) => {
            const isComplete = index <= currentIndex;
            const isCurrent = index === currentIndex;
            const config = statusConfig[step.key] || statusConfig.pending;
            const Icon = config.icon;

            return (
              <div key={step.key} className='flex flex-col items-center gap-2'>
                <div
                  className={cn(
                    'w-8 h-8 rounded-full flex items-center justify-center border-2 transition-all duration-300',
                    isComplete
                      ? 'bg-primary border-primary text-primary-foreground'
                      : 'bg-background border-muted text-muted-foreground'
                  )}>
                  {isComplete ? <Check className='w-4 h-4' /> : <Icon className='w-4 h-4' />}
                </div>
                <span
                  className={cn(
                    'text-xs font-medium',
                    isCurrent ? 'text-primary font-semibold' : 'text-muted-foreground'
                  )}>
                  {step.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
