'use client';

import clsx from 'clsx';
import { Minus, Plus } from 'lucide-react';
import React, { useState } from 'react';

import { updateCart, removeFromCart } from '@/lib/sfcc';

import { Loader } from '../ui/feedback/loader';

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

export function EditItemQuantityButton({ item, type, optimisticUpdate }) {
  const [isLoading, setIsLoading] = useState(false);
  const merchandiseId = item.merchandise.id;

  const handleUpdate = async (e) => {
    e.preventDefault();
    const newQuantity = type === 'plus' ? item.quantity + 1 : item.quantity - 1;

    // Optimistic update
    optimisticUpdate(merchandiseId, type);

    setIsLoading(true);
    try {
      if (newQuantity <= 0) {
        if (item.id) await removeFromCart([item.id]);
      } else {
        await updateCart([
          {
            id: item.id,
            merchandiseId,
            quantity: newQuantity,
          },
        ]);
      }
    } catch (error) {
      console.error('Failed to update quantity', error);
    } finally {
      setIsLoading(false);
    }
  };

  return <QuantityButton type={type} onClick={handleUpdate} loading={isLoading} />;
}
