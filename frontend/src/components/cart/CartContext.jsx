'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import { cartApi } from '@/lib/apiClient';
import { getToken } from '@/lib/apiClient';

const CartContext = createContext(undefined);

function createEmptyCart() {
  return {
    id: undefined,
    items: [],
    totalQuantity: 0,
    totalPrice: '0',
  };
}

function computeTotals(items) {
  const totalQuantity = items.reduce((sum, item) => sum + item.quantity, 0);
  const totalPrice = items
    .reduce((sum, item) => sum + Number(item.book.price) * item.quantity, 0)
    .toFixed(2);
  return { totalQuantity, totalPrice };
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState(createEmptyCart());
  const [loading, setLoading] = useState(true);
  const [justAdded, setJustAdded] = useState(false);

  const fetchCart = useCallback(async () => {
    if (!getToken()) {
      setCart(createEmptyCart());
      setLoading(false);
      return;
    }
    try {
      const response = await cartApi.getMyCart();
      const data = response.data;
      const items = data.items || [];
      const { totalQuantity, totalPrice } = computeTotals(items);
      setCart({ id: data.id, items, totalQuantity, totalPrice });
    } catch {
      setCart(createEmptyCart());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const addToCart = useCallback(async (bookId, quantity = 1) => {
    if (!getToken()) return;
    try {
      const response = await cartApi.addCartItem({
        addCartItemRequest: { bookId, quantity },
      });
      const newItem = response.data;
      setCart((prev) => {
        const existingIndex = prev.items.findIndex((item) => item.bookId === newItem.bookId);
        let updatedItems;
        if (existingIndex >= 0) {
          updatedItems = prev.items.map((item, i) => (i === existingIndex ? newItem : item));
        } else {
          updatedItems = [...prev.items, newItem];
        }
        const { totalQuantity, totalPrice } = computeTotals(updatedItems);
        return { ...prev, items: updatedItems, totalQuantity, totalPrice };
      });
      setJustAdded(true);
    } catch (error) {
      console.error('Failed to add to cart', error);
      throw error;
    }
  }, []);

  const removeFromCart = useCallback(async (itemId) => {
    if (!getToken()) return;
    try {
      await cartApi.removeCartItem({ itemId });
      setCart((prev) => {
        const updatedItems = prev.items.filter((item) => item.id !== itemId);
        const { totalQuantity, totalPrice } = computeTotals(updatedItems);
        return { ...prev, items: updatedItems, totalQuantity, totalPrice };
      });
    } catch (error) {
      console.error('Failed to remove from cart', error);
      throw error;
    }
  }, []);

  const updateQuantity = useCallback(async (itemId, quantity) => {
    if (!getToken()) return;
    try {
      const response = await cartApi.updateCartItemQuantity({
        itemId,
        updateCartItemQuantityRequest: { quantity },
      });
      const updatedItem = response.data;
      setCart((prev) => {
        const updatedItems = prev.items.map((item) => (item.id === itemId ? updatedItem : item));
        const { totalQuantity, totalPrice } = computeTotals(updatedItems);
        return { ...prev, items: updatedItems, totalQuantity, totalPrice };
      });
    } catch (error) {
      console.error('Failed to update quantity', error);
      throw error;
    }
  }, []);

  const clearCart = useCallback(async () => {
    if (!getToken()) return;
    try {
      await cartApi.clearAllCartItems();
      setCart(createEmptyCart());
    } catch (error) {
      console.error('Failed to clear cart', error);
      throw error;
    }
  }, []);

  const clearJustAdded = useCallback(() => setJustAdded(false), []);

  const value = useMemo(
    () => ({
      cart,
      loading,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      refreshCart: fetchCart,
      justAdded,
      clearJustAdded,
    }),
    [
      cart,
      loading,
      addToCart,
      removeFromCart,
      updateQuantity,
      clearCart,
      fetchCart,
      justAdded,
      clearJustAdded,
    ]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error('useCart must be used within a CartProvider');
  }
  return context;
}
