'use client';

import { PlusCircleIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useState } from 'react';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { Loader } from '@/components/ui/feedback/loader';
import { Button } from '@/components/ui/forms/button';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/overlays/tooltip';

export function AddToCart({
  bookId,
  available = true,
  className,
  iconOnly = false,
  icon = <PlusCircleIcon />,
  ...buttonProps
}) {
  const { addToCart } = useCart();
  const [isLoading, setIsLoading] = useState(false);

  const handleAddToCart = async (e) => {
    e.preventDefault();
    if (!bookId || !available) return;

    setIsLoading(true);
    try {
      await addToCart(bookId, 1);
      toast.success('Added to cart');
    } catch {
      toast.error('Failed to add to cart');
    } finally {
      setIsLoading(false);
    }
  };

  const getButtonText = () => {
    if (!available) return 'Out Of Stock';
    if (isLoading) return 'Adding...';
    return 'Add To Bag';
  };

  const isDisabled = !available || isLoading || !bookId;

  const getLoaderSize = () => {
    const buttonSize = buttonProps.size;
    if (buttonSize === 'sm' || buttonSize === 'icon-sm' || buttonSize === 'icon') return 'sm';
    if (buttonSize === 'icon-lg') return 'default';
    if (buttonSize === 'lg') return 'lg';
    return 'default';
  };

  const buttonElement = (
    <Button
      type='button'
      onClick={handleAddToCart}
      aria-label={!bookId ? 'Select a book' : 'Add to bag'}
      disabled={isDisabled}
      className={iconOnly ? undefined : 'w-full relative flex items-center justify-between'}
      {...buttonProps}>
      <AnimatePresence initial={false} mode='wait'>
        {iconOnly ? (
          <motion.div
            key={isLoading ? 'loading' : 'icon'}
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
            className='flex items-center justify-center'>
            {isLoading ? (
              <Loader size={getLoaderSize()} />
            ) : (
              <span className='inline-block'>{icon}</span>
            )}
          </motion.div>
        ) : (
          <motion.div
            key={isLoading ? 'loading' : getButtonText()}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className='w-full flex items-center justify-center'>
            {isLoading ? (
              <Loader size={getLoaderSize()} />
            ) : (
              <div className='w-full flex items-center justify-between'>
                <span className='font-sans font-bold uppercase tracking-tight'>
                  {getButtonText()}
                </span>
                <PlusCircleIcon />
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </Button>
  );

  return (
    <div className={className}>
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
    </div>
  );
}
