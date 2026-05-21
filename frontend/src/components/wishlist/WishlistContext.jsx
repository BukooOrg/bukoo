'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { useCart } from '@/components/cart/CartContext';
import { wishlistApi } from '@/lib/apiClient';
import { getToken } from '@/lib/apiClient';

const WishlistContext = createContext(undefined);

function createEmptyWishlist() {
  return {
    id: undefined,
    items: [],
  };
}

export function WishlistProvider({ children }) {
  const [wishlist, setWishlist] = useState(createEmptyWishlist());
  const [loading, setLoading] = useState(true);
  const { refreshCart } = useCart();

  const fetchWishlist = useCallback(async () => {
    if (!getToken()) {
      setWishlist(createEmptyWishlist());
      setLoading(false);
      return;
    }
    try {
      const response = await wishlistApi.getMyWishlist();
      const data = response.data;
      setWishlist({ id: data.id, items: data.items || [] });
    } catch {
      setWishlist(createEmptyWishlist());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWishlist();
  }, [fetchWishlist]);

  const addToWishlist = useCallback(async (bookId) => {
    if (!getToken()) return;
    try {
      const response = await wishlistApi.addWishlistItem({
        addWishlistItemRequest: { bookId },
      });
      const newItem = response.data;
      setWishlist((prev) => ({
        ...prev,
        items: [...prev.items, newItem],
      }));
    } catch (error) {
      console.error('Failed to add to wishlist', error);
      throw error;
    }
  }, []);

  const removeFromWishlist = useCallback(async (itemId) => {
    if (!getToken()) return;
    try {
      await wishlistApi.removeWishlistItem({ itemId });
      setWishlist((prev) => ({
        ...prev,
        items: prev.items.filter((item) => item.id !== itemId),
      }));
    } catch (error) {
      console.error('Failed to remove from wishlist', error);
      throw error;
    }
  }, []);

  const moveToCart = useCallback(
    async (itemId) => {
      if (!getToken()) return;
      try {
        await wishlistApi.moveWishlistItemToCart({ itemId });
        setWishlist((prev) => ({
          ...prev,
          items: prev.items.filter((item) => item.id !== itemId),
        }));
        await refreshCart();
      } catch (error) {
        console.error('Failed to move item to cart', error);
        throw error;
      }
    },
    [refreshCart]
  );

  const isInWishlist = useCallback(
    (bookId) => wishlist.items.some((item) => item.bookId === bookId),
    [wishlist.items]
  );

  const value = useMemo(
    () => ({
      wishlist,
      loading,
      addToWishlist,
      removeFromWishlist,
      moveToCart,
      isInWishlist,
      refreshWishlist: fetchWishlist,
    }),
    [wishlist, loading, addToWishlist, removeFromWishlist, moveToCart, isInWishlist, fetchWishlist]
  );

  return <WishlistContext.Provider value={value}>{children}</WishlistContext.Provider>;
}

export function useWishlist() {
  const context = useContext(WishlistContext);
  if (context === undefined) {
    throw new Error('useWishlist must be used within a WishlistProvider');
  }
  return context;
}
