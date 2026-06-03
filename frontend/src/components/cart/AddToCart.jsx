'use client';

import { PlusCircleIcon } from 'lucide-react';
import { motion } from 'motion/react';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { Loader } from '@/components/ui/feedback/loader';
import { Button } from '@/components/ui/forms/button';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/overlays/tooltip';
import { getToken } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

export function AddToCart({
  bookId,
  product,
  available = true,
  className,
  iconOnly = false,
  icon = <PlusCircleIcon />,
  ...buttonProps
}) {
  const { addToCart } = useCart();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [pulse, setPulse] = useState(false);

  const resolvedBookId = bookId || product?.id;

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!resolvedBookId || !available) return;

    if (!getToken()) {
      navigate('/login', { state: { from: window.location.pathname } });
      return;
    }

    setIsLoading(true);
    try {
      await addToCart(resolvedBookId, 1);
      toast.success('Added to cart');
      setPulse(true);
      setTimeout(() => setPulse(false), 300);
    } catch {
      toast.error('Failed to add to cart');
    } finally {
      setIsLoading(false);
    }
  };

  const getButtonText = () => {
    if (!available) return 'Out Of Stock';
    if (isLoading) return 'Adding...';
    return 'Add to cart';
  };

  const isDisabled = !available || isLoading || !resolvedBookId;

  const getLoaderSize = () => {
    const buttonSize = buttonProps.size;
    if (buttonSize === 'sm' || buttonSize === 'icon-sm' || buttonSize === 'icon') return 'sm';
    if (buttonSize === 'icon-lg') return 'default';
    if (buttonSize === 'lg') return 'lg';
    return 'default';
  };

  const buttonElement = (
    <motion.div
      animate={pulse ? { scale: [1, 1.05, 1] } : {}}
      transition={{ duration: 0.3, ease: 'easeOut' }}>
      <Button
        type='button'
        onClick={handleAddToCart}
        aria-label={!resolvedBookId ? 'Select a book' : 'Add to bag'}
        disabled={isDisabled}
        className={
          iconOnly ? className : cn('w-full relative flex items-center justify-between', className)
        }
        {...buttonProps}>
        {isLoading ? (
          <Loader size={getLoaderSize()} />
        ) : iconOnly ? (
          <span className='inline-block'>{icon}</span>
        ) : (
          <div className='w-full flex items-center justify-center gap-3'>
            <span className='font-sans font-bold uppercase tracking-tight'>{getButtonText()}</span>
            <PlusCircleIcon />
          </div>
        )}
      </Button>
    </motion.div>
  );

  return (
    <>
      {!available ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <div className='w-full'>{buttonElement}</div>
          </TooltipTrigger>
          <TooltipContent portal={false} className='pointer-events-none'>
            <span className='relative z-10'>This book is currently unavailable</span>
          </TooltipContent>
        </Tooltip>
      ) : (
        buttonElement
      )}
    </>
  );
}
