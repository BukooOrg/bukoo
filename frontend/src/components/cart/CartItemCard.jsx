'use client';

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { ConfirmDialog } from '@/components/cart/ConfirmDialog';

import { EditItemQuantityButton } from './EditItemQuantityButton';

export function CartItemCard({ item }) {
  const { removeFromCart } = useCart();
  const [removeDialog, setRemoveDialog] = useState(false);
  const [removing, setRemoving] = useState(false);

  const subtotal = (Number(item.book.price) * item.quantity).toFixed(2);

  const handleRemove = async () => {
    setRemoving(true);
    try {
      await removeFromCart(item.id);
      toast.success('Removed from cart');
    } catch {
      toast.error('Failed to remove item');
    } finally {
      setRemoving(false);
      setRemoveDialog(false);
    }
  };

  return (
    <>
      <div className='flex gap-8 p-8 border border-gray-200 rounded-lg bg-white'>
        <div className='w-32 h-44 shrink-0 overflow-hidden rounded bg-gray-100'>
          {item.book.coverUrl ? (
            <img
              src={item.book.coverUrl}
              alt={item.book.title}
              className='w-full h-full object-cover'
            />
          ) : (
            <div className='w-full h-full flex items-center justify-center text-gray-400 text-base'>
              No cover
            </div>
          )}
        </div>

        <div className='flex-1 min-w-0'>
          <Link
            to={`/product/${item.bookId}`}
            className='text-2xl font-medium font-serif hover:underline line-clamp-1'>
            {item.book.title}
          </Link>
          <p className='text-lg text-gray-500 mt-2'>RM {item.book.price}</p>

          <div className='flex items-center justify-between mt-6'>
            <div className='flex items-center gap-3'>
              <EditItemQuantityButton item={item} type='minus' setRemoveDialog={setRemoveDialog} />
              <span className='w-10 text-center text-lg'>{item.quantity}</span>
              <EditItemQuantityButton item={item} type='plus' />
            </div>
            <div className='flex items-center gap-6'>
              <span className='text-xl font-medium'>RM {subtotal}</span>
              <button
                onClick={() => setRemoveDialog(true)}
                className='text-base text-gray-400 hover:text-red-600'>
                Remove
              </button>
            </div>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={removeDialog}
        onOpenChange={setRemoveDialog}
        title='Remove from cart?'
        description={`This will remove "${item.book.title}" from your cart.`}
        onConfirm={handleRemove}
        loading={removing}
      />
    </>
  );
}
