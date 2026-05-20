'use client';

import clsx from 'clsx';
import { Minus, Plus } from 'lucide-react';
import React, { useState } from 'react';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { Loader } from '@/components/ui/feedback/loader';

function QuantityButton({ type, onClick, disabled, loading }) {
  return (
    <button
      type='button'
      onClick={onClick}
      disabled={disabled || loading}
      aria-label={type === 'plus' ? 'Increase item quantity' : 'Reduce item quantity'}
      className={clsx(
        'ease flex h-full min-w-[36px] max-w-[36px] flex-none items-center justify-center rounded-full p-2 transition-all duration-200 hover:border-neutral-800 hover:opacity-80 disabled:opacity-30',
        {
          'ml-auto': type === 'minus',
        }
      )}>
      {loading ? (
        <Loader size='sm' />
      ) : type === 'plus' ? (
        <Plus className='h-4 w-4 dark:text-neutral-500' />
      ) : (
        <Minus className='h-4 w-4 dark:text-neutral-500' />
      )}
    </button>
  );
}

export function EditItemQuantityButton({ item, type }) {
  const { updateQuantity } = useCart();
  const [isLoading, setIsLoading] = useState(false);

  const handleUpdate = async (e) => {
    e.preventDefault();
    const newQuantity = type === 'plus' ? item.quantity + 1 : item.quantity - 1;
    if (newQuantity <= 0) return;

    setIsLoading(true);
    try {
      await updateQuantity(item.id, newQuantity);
    } catch {
      toast.error('Failed to update quantity');
    } finally {
      setIsLoading(false);
    }
  };

  return <QuantityButton type={type} onClick={handleUpdate} loading={isLoading} />;
}
