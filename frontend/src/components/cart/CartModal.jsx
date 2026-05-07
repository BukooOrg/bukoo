'use client';

import { ArrowRight, TriangleAlert, PlusCircleIcon, ShoppingBag } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { formatPrice } from '@/lib/sfcc/utils';

import { Button } from '../ui/forms/button';

import { useCart } from './CartContext';
import { CartItemCard } from './CartItemCard';

const CartItems = ({ closeCart }) => {
  const { cart, updateCartItem } = useCart();
  const navigate = useNavigate();

  if (!cart) return <></>;

  const handleCheckout = (e) => {
    e.preventDefault();
    closeCart();
    navigate('/checkout');
  };

  return (
    <div className='flex flex-col justify-between h-full overflow-hidden'>
      <div className='flex justify-between px-2 text-sm text-muted-foreground'>
        <span>Products</span>
        <span>{cart.lines.length} items</span>
      </div>
      <div className='py-4 space-y-3 overflow-auto grow'>
        <AnimatePresence>
          {cart.lines
            .sort((a, b) => a.merchandise.product.title.localeCompare(b.merchandise.product.title))
            .map((item, i) => (
              <motion.div
                key={`${item.id}-${item.merchandise.id}`}
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, delay: i * 0.1, ease: 'easeOut' }}>
                <CartItemCard
                  item={item}
                  optimisticUpdate={updateCartItem}
                  onCloseCart={closeCart}
                />
              </motion.div>
            ))}
        </AnimatePresence>
      </div>
      <div className='py-4 text-sm text-neutral-500 dark:text-neutral-400'>
        <div className='flex items-center justify-between pb-1 mb-3 border-b border-neutral-200 dark:border-neutral-700'>
          <p>Taxes</p>
          <p className='text-base text-right text-black dark:text-white'>
            {formatPrice(cart.cost.totalTaxAmount.amount, cart.cost.totalTaxAmount.currencyCode)}
          </p>
        </div>
        <div className='flex items-center justify-between pt-1 pb-1 mb-3 border-b border-neutral-200 dark:border-neutral-700'>
          <p>Shipping</p>
          {cart.cost.shippingAmount ? (
            <p className='text-base text-right text-black dark:text-white'>
              {formatPrice(cart.cost.shippingAmount.amount, cart.cost.shippingAmount.currencyCode)}
            </p>
          ) : (
            <p className='text-right'>Calculated at checkout</p>
          )}
        </div>
        <div className='flex items-center justify-between pt-1 pb-1 mb-3 border-b border-neutral-200 dark:border-neutral-700'>
          <p>Total</p>
          <p className='text-base text-right text-black dark:text-white'>
            {formatPrice(cart.cost.totalAmount.amount, cart.cost.totalAmount.currencyCode)}
          </p>
        </div>
      </div>
      <Button
        onClick={handleCheckout}
        size='lg'
        className='relative flex items-center justify-between w-full gap-3 bg-primary text-secondary'>
        Proceed to Checkout
        <ArrowRight className='size-6' />
      </Button>
    </div>
  );
};

export default function CartModal() {
  const { cart, mode } = useCart();
  const [isOpen, setIsOpen] = useState(false);
  const quantityRef = useRef(cart?.totalQuantity);
  const openCart = () => setIsOpen(true);
  const closeCart = () => setIsOpen(false);
  const { pathname } = useLocation();

  useEffect(() => {
    if (
      cart?.totalQuantity &&
      cart?.totalQuantity !== quantityRef.current &&
      cart?.totalQuantity > 0
    ) {
      if (!isOpen) {
        setIsOpen(true);
      }
      quantityRef.current = cart?.totalQuantity;
    }
  }, [isOpen, cart?.totalQuantity]);

  useEffect(() => {
    if (pathname === '/checkout') closeCart();
  }, [pathname]);

  const renderCartContent = () => {
    if (mode === 'mock') {
      return (
        <div className='flex flex-col items-center justify-center w-full mt-20 overflow-hidden'>
          <TriangleAlert className='size-12' />
          <p className='mt-6 text-2xl font-semibold text-center'>
            Cart is not available in mock mode.
          </p>
          <p className='mt-2 text-sm text-center text-muted-foreground'>Complete the SFCC setup.</p>
        </div>
      );
    }

    if (!cart || cart.lines.length === 0) {
      return (
        <AnimatePresence mode='wait'>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.3, ease: 'easeInOut' }}
            className='flex w-full'>
            <Link
              to='/shop'
              className='w-full p-2 border border-dashed rounded-none bg-card border-secondary/40'
              onClick={closeCart}>
              <div className='flex flex-row gap-6 p-4'>
                <div className='relative flex items-center justify-center overflow-hidden border border-dashed rounded-sm size-20 shrink-0 border-secondary/40'>
                  <PlusCircleIcon className='size-6 text-primary/40' />
                </div>
                <div className='flex flex-col justify-center flex-1 gap-2 2xl:gap-3'>
                  <span className='font-serif text-2xl font-black text-primary'>Bag is empty</span>
                  <p className='font-sans text-sm italic font-bold opacity-60 hover:underline'>
                    Find your next favorite story
                  </p>
                </div>
              </div>
            </Link>
          </motion.div>
        </AnimatePresence>
      );
    }

    return <CartItems closeCart={closeCart} />;
  };

  return (
    <>
      <Button
        aria-label='Open bag'
        onClick={openCart}
        variant='ghost'
        size='icon'
        className='relative transition-colors text-primary hover:bg-primary/10'>
        <ShoppingBag className='size-5' />
        {(cart?.totalQuantity || 0) > 0 && (
          <span className='absolute -top-1 -right-1 size-4 flex items-center justify-center text-[9px] font-black bg-primary text-background rounded-full'>
            {cart.totalQuantity}
          </span>
        )}
      </Button>
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className='fixed inset-0 z-50 transition-all duration-300 bg-background/40 backdrop-blur-md'
              onClick={closeCart}
              aria-hidden='true'
            />

            {/* Panel */}
            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className='fixed top-0 bottom-0 right-0 flex w-full md:w-[480px] p-4 z-50'>
              <div className='flex flex-col bg-white/80 backdrop-blur-3xl rounded-[40px] border border-white/40 shadow-2xl w-full h-full overflow-hidden'>
                {/* Fixed Header Row */}
                <div className='relative z-20 flex items-center justify-between p-8 border-b md:p-10 border-primary/5 bg-white/40 backdrop-blur-md'>
                  <h2 className='font-serif text-4xl font-black tracking-tighter text-primary'>
                    Your Bag
                  </h2>
                  <Button
                    size='sm'
                    variant='ghost'
                    aria-label='Close bag'
                    onClick={closeCart}
                    className='font-sans font-black uppercase text-xs tracking-[0.2em] opacity-40 hover:opacity-100 transition-opacity'>
                    Close
                  </Button>
                </div>

                <div className='flex-1 p-8 pt-6 overflow-hidden md:p-10'>{renderCartContent()}</div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
