'use client';

import React, { useState } from 'react';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { ConfirmDialog } from '@/components/cart/ConfirmDialog';

export function EditItemQuantityButton({ item, type, setRemoveDialog }) {
  const { updateQuantity, removeFromCart } = useCart();
  const [isLoading, setIsLoading] = useState(false);
  const [removeDialog, setLocalRemoveDialog] = useState(false);

  const handleUpdate = async (e) => {
    e.preventDefault();
    const newQuantity = type === 'plus' ? item.quantity + 1 : item.quantity - 1;

    if (newQuantity <= 0) {
      if (setRemoveDialog) {
        setRemoveDialog(true);
      } else {
        setLocalRemoveDialog(true);
      }
      return;
    }

    setIsLoading(true);
    try {
      await updateQuantity(item.id, newQuantity);
    } catch {
      toast.error('Failed to update quantity');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRemove = async () => {
    setIsLoading(true);
    try {
      await removeFromCart(item.id);
      toast.success('Removed from cart');
    } catch {
      toast.error('Failed to remove item');
    } finally {
      setIsLoading(false);
      setLocalRemoveDialog(false);
    }
  };

  return (
    <>
      <button
        type='button'
        onClick={handleUpdate}
        disabled={isLoading}
        className='w-10 h-10 flex items-center justify-center text-lg text-gray-500 hover:text-black border border-gray-200 rounded disabled:opacity-30'>
        {type === 'plus' ? '+' : '−'}
      </button>

      <ConfirmDialog
        open={removeDialog}
        onOpenChange={setLocalRemoveDialog}
        title='Remove from cart?'
        description={`This will remove "${item.book.title}" from your cart.`}
        onConfirm={handleRemove}
        loading={isLoading}
      />
    </>
  );
}
