import { Loader2Icon } from 'lucide-react';

import { cn } from '@/lib/utils';

const sizeMap = {
  sm: 'size-3',
  md: 'size-4',
  lg: 'size-6',
  xl: 'size-8',
};

function Spinner({ className, size = 'md', ...props }) {
  return (
    <Loader2Icon
      role='status'
      aria-label='Loading'
      className={cn(sizeMap[size] || sizeMap.md, 'animate-spin', className)}
      {...props}
    />
  );
}

export { Spinner };
