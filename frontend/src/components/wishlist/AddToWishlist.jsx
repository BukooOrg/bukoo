'use client';

import { Heart } from 'lucide-react';
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';

import { useWishlist } from '@/components/wishlist/WishlistContext';
import { getToken } from '@/lib/apiClient';
import { cn } from '@/lib/utils';

export function AddToWishlist({ bookId, className, size = 'default' }) {
  const { addToWishlist, removeFromWishlist, isInWishlist, wishlist } = useWishlist();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);

  const inWishlist = isInWishlist(bookId);

  const handleClick = async (e) => {
    e.preventDefault();
    e.stopPropagation();

    if (!getToken()) {
      navigate('/login', { state: { from: window.location.pathname } });
      return;
    }

    setIsLoading(true);
    try {
      if (inWishlist) {
        const found = wishlist.items.find((i) => i.bookId === bookId);
        if (found) {
          await removeFromWishlist(found.id);
          toast.success('Removed from wishlist');
        }
      } else {
        await addToWishlist(bookId);
        toast.success('Added to wishlist');
      }
    } catch {
      toast.error('Failed to update wishlist');
    } finally {
      setIsLoading(false);
    }
  };

  const sizeClasses = {
    sm: 'size-4',
    default: 'size-5',
    lg: 'size-6',
  };

  const buttonSizeClasses = {
    sm: 'w-8 h-8',
    default: 'w-10 h-10',
    lg: 'w-12 h-12',
  };

  return (
    <button
      type='button'
      onClick={handleClick}
      disabled={isLoading}
      aria-label={inWishlist ? 'Remove from wishlist' : 'Add to wishlist'}
      className={cn(
        'flex items-center justify-center rounded-full border border-gray-200 transition-all hover:border-black disabled:opacity-40',
        buttonSizeClasses[size],
        inWishlist && 'bg-black border-black',
        className
      )}>
      <Heart
        className={cn(
          'transition-colors',
          sizeClasses[size],
          inWishlist ? 'text-white fill-white' : 'text-gray-400'
        )}
      />
    </button>
  );
}
