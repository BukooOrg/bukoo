'use client';

import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { ConfirmDialog } from '@/components/cart/ConfirmDialog';
import { useWishlist } from '@/components/wishlist/WishlistContext';

export function WishlistItemCard({ item }) {
  const { removeFromWishlist, moveToCart } = useWishlist();
  const [removeDialog, setRemoveDialog] = useState(false);
  const [moving, setMoving] = useState(false);
  const [removing, setRemoving] = useState(false);

  const handleMoveToCart = async () => {
    setMoving(true);
    try {
      await moveToCart(item.id);
      toast.success('Moved to cart');
    } catch {
      toast.error('Failed to move to cart');
    } finally {
      setMoving(false);
    }
  };

  const handleRemove = async () => {
    setRemoving(true);
    try {
      await removeFromWishlist(item.id);
      toast.success('Removed from wishlist');
    } catch {
      toast.error('Failed to remove item');
    } finally {
      setRemoving(false);
      setRemoveDialog(false);
    }
  };

  return (
    <>
      <div className='flex flex-col border border-primary/5 rounded-lg bg-white overflow-hidden'>
        <Link
          to={`/product/${item.bookId}`}
          className='block aspect-[3/4] overflow-hidden bg-primary/5'>
          {item.book.coverUrl ? (
            <img
              src={item.book.coverUrl}
              alt={item.book.title}
              className='w-full h-full object-cover hover:scale-105 transition-transform duration-500'
            />
          ) : (
            <div className='w-full h-full flex items-center justify-center text-primary/40 text-base'>
              No cover
            </div>
          )}
        </Link>

        <div className='p-6 flex flex-col flex-1'>
          <Link
            to={`/product/${item.bookId}`}
            className='text-xl font-medium font-serif hover:underline line-clamp-2'>
            {item.book.title}
          </Link>
          <p className='text-lg text-primary/40 mt-2'>RM {item.book.price}</p>

          <div className='flex items-center gap-3 mt-auto pt-4'>
            <button
              onClick={handleMoveToCart}
              disabled={moving}
              className='flex-1 h-12 bg-primary text-secondary text-base font-medium rounded hover:bg-primary/90 transition-colors disabled:opacity-40'>
              {moving ? 'Moving...' : 'Move to Cart'}
            </button>
            <button
              onClick={() => setRemoveDialog(true)}
              disabled={removing}
              className='h-12 px-4 border border-primary/5 text-base text-primary/40 hover:text-destructive hover:border-destructive/30 rounded transition-colors disabled:opacity-40'>
              Remove
            </button>
          </div>
        </div>
      </div>

      <ConfirmDialog
        open={removeDialog}
        onOpenChange={setRemoveDialog}
        title='Remove from wishlist?'
        description={`This will remove "${item.book.title}" from your wishlist.`}
        onConfirm={handleRemove}
        loading={removing}
      />
    </>
  );
}
