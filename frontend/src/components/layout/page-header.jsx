import { ArrowLeft } from 'lucide-react';
import React from 'react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/forms/button';
import { cn } from '@/lib/utils';

export function PageHeader({
  className,
  title,
  subtitle,
  backTo,
  backLabel = 'Back',
  actions,
  breadcrumb,
  ...props
}) {
  const navigate = useNavigate();

  return (
    <header className={cn('mb-8', className)} {...props}>
      {breadcrumb}

      <div className='flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between'>
        <div className='flex-1 min-w-0'>
          {backTo && (
            <Button
              variant='ghost'
              size='sm'
              className='mb-2 -ml-2 text-muted-foreground hover:text-foreground'
              onClick={() => navigate(backTo)}>
              <ArrowLeft className='w-4 h-4 mr-1.5' />
              {backLabel}
            </Button>
          )}

          <h1 className='font-serif text-3xl font-bold text-primary tracking-tight'>{title}</h1>

          {subtitle && <p className='mt-1 text-base text-muted-foreground'>{subtitle}</p>}
        </div>

        {actions && <div className='flex items-center gap-2 shrink-0'>{actions}</div>}
      </div>
    </header>
  );
}
