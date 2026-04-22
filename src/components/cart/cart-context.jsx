"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useState
} from "react";
import { getCart } from "@/lib/sfcc";

const CartContext = createContext(undefined);

function calculateItemCost(quantity, price) {
  return (Number(price) * quantity).toString();
}

function updateCartItemHelper(item, updateType) {
  if (updateType === "delete") return null;

  const newQuantity =
    updateType === "plus" ? item.quantity + 1 : item.quantity - 1;
  if (newQuantity === 0) return null;

  const singleItemAmount = Number(item.cost.totalAmount.amount) / item.quantity;
  const newTotalAmount = calculateItemCost(
    newQuantity,
    singleItemAmount.toString()
  );

  return {
    ...item,
    quantity: newQuantity,
    cost: {
      ...item.cost,
      totalAmount: {
        ...item.cost.totalAmount,
        amount: newTotalAmount
      }
    }
  };
}

function createOrUpdateCartItem(existingItem, variant, product) {
  const quantity = existingItem ? existingItem.quantity + 1 : 1;
  const totalAmount = calculateItemCost(quantity, variant.price.amount);

  return {
    id: existingItem?.id,
    quantity,
    cost: {
      totalAmount: {
        amount: totalAmount,
        currencyCode: variant.price.currencyCode
      }
    },
    merchandise: {
      id: variant.id,
      title: variant.title,
      selectedOptions: variant.selectedOptions,
      product: {
        id: product.id,
        handle: product.handle,
        title: product.title,
        featuredImage: product.featuredImage,
        images: product.images,
        variationValues: product.variationValues,
        description: product.description
      }
    }
  };
}

function updateCartTotals(lines) {
  const totalQuantity = lines.reduce((sum, item) => sum + item.quantity, 0);
  const totalAmount = lines.reduce(
    (sum, item) => sum + Number(item.cost.totalAmount.amount),
    0
  );
  const currencyCode = lines[0]?.cost.totalAmount.currencyCode ?? "USD";

  return {
    totalQuantity,
    cost: {
      subtotalAmount: { amount: totalAmount.toString(), currencyCode },
      totalAmount: { amount: totalAmount.toString(), currencyCode },
      totalTaxAmount: { amount: "0", currencyCode }
    }
  };
}

function createEmptyCart() {
  return {
    id: undefined,
    checkoutUrl: "https://your-checkout-url.com",
    totalQuantity: 0,
    lines: [],
    cost: {
      subtotalAmount: { amount: "0", currencyCode: "USD" },
      totalAmount: { amount: "0", currencyCode: "USD" },
      totalTaxAmount: { amount: "0", currencyCode: "USD" }
    }
  };
}

function cartReducer(state, action) {
  const currentCart = state || createEmptyCart();

  switch (action.type) {
    case "SET_CART":
      return action.payload || createEmptyCart();
    case "UPDATE_ITEM": {
      const { merchandiseId, updateType } = action.payload;
      const updatedLines = currentCart.lines.map((item) =>
        item.merchandise.id === merchandiseId ?
          updateCartItemHelper(item, updateType) :
          item
      ).filter(Boolean);

      if (updatedLines.length === 0) {
        return {
          ...currentCart,
          lines: [],
          totalQuantity: 0,
          cost: {
            ...currentCart.cost,
            totalAmount: { ...currentCart.cost.totalAmount, amount: "0" }
          }
        };
      }

      return {
        ...currentCart,
        ...updateCartTotals(updatedLines),
        lines: updatedLines
      };
    }
    case "ADD_ITEM": {
      const { variant, product } = action.payload;
      const existingItem = currentCart.lines.find(
        (item) => item.merchandise.id === variant.id
      );
      const updatedItem = createOrUpdateCartItem(
        existingItem,
        variant,
        product
      );

      const updatedLines = existingItem ?
        currentCart.lines.map((item) =>
          item.merchandise.id === variant.id ? updatedItem : item
        ) :
        [...currentCart.lines, updatedItem];

      return {
        ...currentCart,
        ...updateCartTotals(updatedLines),
        lines: updatedLines
      };
    }
    default:
      return currentCart;
  }
}

export function CartProvider({ children }) {
  const [cart, dispatch] = useReducer(cartReducer, createEmptyCart());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadCart() {
      try {
        const initialCart = await getCart();
        dispatch({ type: "SET_CART", payload: initialCart });
      } catch (error) {
        console.error("Failed to load cart", error);
      } finally {
        setLoading(false);
      }
    }
    loadCart();
  }, []);

  const updateCartItem = useCallback((merchandiseId, updateType) => {
    dispatch({
      type: "UPDATE_ITEM",
      payload: { merchandiseId, updateType }
    });
  }, []);

  const addCartItem = useCallback((variant, product) => {
    dispatch({ type: "ADD_ITEM", payload: { variant, product } });
  }, []);

  const value = useMemo(() => ({
    cart,
    loading,
    updateCartItem,
    addCartItem
  }), [cart, loading, updateCartItem, addCartItem]);

  return (
    <CartContext.Provider value={value}>
      {children}
    </CartContext.Provider>
  );
}

export function useCart() {
  const context = useContext(CartContext);
  if (context === undefined) {
    throw new Error("useCart must be used within a CartProvider");
  }
  return context;
}