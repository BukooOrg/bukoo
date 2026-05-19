import { AlertTriangle, Loader2 } from 'lucide-react';
import React from 'react';

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/feedback/alert-dialog';
import { Button } from '@/components/ui/forms/button';
import { cn } from '@/lib/utils';

export function ConfirmDialog({
  open,
  onOpenChange,
  title = 'Are you sure?',
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  variant = 'default',
  loading = false,
  icon,
  children,
}) {
  const Icon = icon || (variant === 'destructive' ? AlertTriangle : null);

  return (
    <AlertDialog open={open} onOpenChange={onOpenChange}>
      {children && <AlertDialogTrigger asChild>{children}</AlertDialogTrigger>}

      <AlertDialogContent>
        {Icon && (
          <div className='flex items-center justify-center w-12 h-12 rounded-full bg-destructive/10 mx-auto'>
            <Icon className='w-6 h-6 text-destructive' />
          </div>
        )}

        <AlertDialogHeader>
          <AlertDialogTitle>{title}</AlertDialogTitle>
          <AlertDialogDescription>{description}</AlertDialogDescription>
        </AlertDialogHeader>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={loading}>{cancelText}</AlertDialogCancel>
          <AlertDialogAction
            onClick={onConfirm}
            disabled={loading}
            className={cn(variant === 'destructive' && 'bg-destructive hover:bg-destructive/90')}>
            {loading ? (
              <>
                <Loader2 className='w-4 h-4 animate-spin' />
                Processing...
              </>
            ) : (
              confirmText
            )}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

export function ConfirmButton({
  title,
  description,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  onConfirm,
  variant = 'default',
  loading = false,
  icon,
  children,
  className,
  ...buttonProps
}) {
  const [open, setOpen] = React.useState(false);

  const handleConfirm = async () => {
    await onConfirm?.();
    setOpen(false);
  };

  return (
    <>
      {children ? (
        React.cloneElement(children, {
          onClick: (e) => {
            children.props?.onClick?.(e);
            setOpen(true);
          },
        })
      ) : (
        <Button
          variant={variant}
          className={className}
          onClick={() => setOpen(true)}
          {...buttonProps}
        />
      )}

      <ConfirmDialog
        open={open}
        onOpenChange={setOpen}
        title={title}
        description={description}
        confirmText={confirmText}
        cancelText={cancelText}
        onConfirm={handleConfirm}
        variant={variant}
        loading={loading}
        icon={icon}
      />
    </>
  );
}
