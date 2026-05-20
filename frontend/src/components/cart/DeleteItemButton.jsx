'use client';

import React, { useState } from 'react';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { Button } from '@/components/ui/forms/button';

export function DeleteItemButton({ item }) {
  const { removeFromCart } = useCart();
  const [loading, setLoading] = useState(false);

  const handleRemove = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await removeFromCart(item.id);
      toast.success('Removed from cart');
    } catch {
      toast.error('Failed to remove item');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      onClick={handleRemove}
      type='button'
      size='sm'
      variant='ghost'
      disabled={loading}
      aria-label='Remove item'
      className='px-2 text-sm text-destructive hover:text-destructive'>
      {loading ? 'Removing...' : 'Remove'}
    </Button>
  );
}
