'use client';

import React, { useState } from 'react';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';

export function DeleteItemButton({ item }) {
  const { removeFromCart } = useCart();
  const [loading, setLoading] = useState(false);

  const handleRemove = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await removeFromCart(item.id);
      toast.success('Removed');
    } catch {
      toast.error('Failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleRemove}
      disabled={loading}
      className='text-base text-gray-400 hover:text-red-600 disabled:opacity-40'>
      {loading ? '...' : 'Remove'}
    </button>
  );
}
