'use client';

import { ArrowRight, PlusCircleIcon, ShoppingBag } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { Button } from '../ui/forms/button';

import { useCart } from './CartContext';

function formatPrice(amount, currency = 'GBP') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

const CartItems = ({ closeCart }) => {
  const { cart, removeFromCart, updateQuantity } = useCart();
  const navigate = useNavigate();

  if (!cart) return <></>;

  const handleCheckout = (e) => {
    e.preventDefault();
    closeCart();
    navigate('/checkout');
  };

  const handleRemove = async (itemId) => {
    try {
      await removeFromCart(itemId);
    } catch {
      console.error('Failed to remove item');
    }
  };

  const handleQuantityChange = async (itemId, newQuantity) => {
    if (newQuantity <= 0) {
      await handleRemove(itemId);
      return;
    }
    try {
      await updateQuantity(itemId, newQuantity);
    } catch {
      console.error('Failed to update quantity');
    }
  };

  return (
    <div className='flex flex-col justify-between h-full overflow-hidden'>
      <div className='flex justify-between px-2 text-sm text-muted-foreground'>
        <span>Products</span>
        <span>{cart.items.length} items</span>
      </div>
      <div className='py-4 space-y-3 overflow-auto grow'>
        <AnimatePresence>
          {cart.items
            .sort((a, b) => a.book.title.localeCompare(b.book.title))
            .map((item, i) => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                transition={{ duration: 0.3, delay: i * 0.1, ease: 'easeOut' }}>
                <CartItemRow
                  item={item}
                  onRemove={handleRemove}
                  onQuantityChange={handleQuantityChange}
                  onCloseCart={closeCart}
                />
              </motion.div>
            ))}
        </AnimatePresence>
      </div>
      <div className='py-4 text-sm text-neutral-500 dark:text-neutral-400'>
        <div className='flex items-center justify-between pt-1 pb-1 mb-3 border-b border-neutral-200 dark:border-neutral-700'>
          <p>Shipping</p>
          <p className='text-right'>Calculated at checkout</p>
        </div>
        <div className='flex items-center justify-between pt-1 pb-1 mb-3 border-b border-neutral-200 dark:border-neutral-700'>
          <p>Total</p>
          <p className='text-base text-right text-black dark:text-white'>
            {formatPrice(cart.totalPrice)}
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

function CartItemRow({ item, onRemove, onQuantityChange, onCloseCart }) {
  const subtotal = (Number(item.book.price) * item.quantity).toFixed(2);

  return (
    <div className='bg-card rounded-lg p-2'>
      <div className='flex flex-row gap-6'>
        <div className='relative size-[120px] overflow-hidden rounded-sm shrink-0 bg-muted'>
          {item.book.coverUrl ? (
            <img
              src={item.book.coverUrl}
              alt={item.book.title}
              className='size-full object-cover'
            />
          ) : (
            <div className='size-full flex items-center justify-center text-muted-foreground text-xs'>
              No cover
            </div>
          )}
        </div>
        <div className='flex flex-col gap-2 2xl:gap-3 flex-1'>
          <Link
            to={`/product/${item.bookId}`}
            onClick={onCloseCart}
            className='z-30 flex flex-col justify-center'>
            <span className='2xl:text-lg font-semibold'>{item.book.title}</span>
          </Link>
          <p className='2xl:text-lg font-semibold'>{formatPrice(subtotal)}</p>
          <div className='flex justify-between items-end mt-auto'>
            <div className='flex h-8 flex-row items-center rounded-md border border-neutral-200 dark:border-neutral-700'>
              <QuantityButton
                onClick={() => onQuantityChange(item.id, item.quantity - 1)}
                type='minus'
              />
              <span className='w-8 text-center text-sm'>{item.quantity}</span>
              <QuantityButton
                onClick={() => onQuantityChange(item.id, item.quantity + 1)}
                type='plus'
              />
            </div>
            <button
              onClick={() => onRemove(item.id)}
              className='px-2 text-sm text-destructive hover:text-destructive/80 -mr-1 -mb-1 opacity-70'
              aria-label='Remove item'>
              Remove
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

function QuantityButton({ type, onClick }) {
  return (
    <button
      type='button'
      onClick={onClick}
      aria-label={type === 'plus' ? 'Increase item quantity' : 'Reduce item quantity'}
      className='ease flex h-full min-w-[36px] max-w-[36px] flex-none items-center justify-center rounded-full p-2 transition-all duration-200 hover:border-neutral-800 hover:opacity-80'>
      {type === 'plus' ? (
        <PlusCircleIcon className='h-4 w-4 dark:text-neutral-500' />
      ) : (
        <MinusIcon className='h-4 w-4 dark:text-neutral-500' />
      )}
    </button>
  );
}

function MinusIcon(props) {
  return (
    <svg
      xmlns='http://www.w3.org/2000/svg'
      width='24'
      height='24'
      viewBox='0 0 24 24'
      fill='none'
      stroke='currentColor'
      strokeWidth='2'
      strokeLinecap='round'
      strokeLinejoin='round'
      {...props}>
      <line x1='5' y1='12' x2='19' y2='12' />
    </svg>
  );
}

export default function CartModal() {
  const { cart } = useCart();
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
    if (!cart || cart.items.length === 0) {
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
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className='fixed inset-0 z-50 transition-all duration-300 bg-background/40 backdrop-blur-md'
              onClick={closeCart}
              aria-hidden='true'
            />

            <motion.div
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ duration: 0.3, ease: 'easeInOut' }}
              className='fixed top-0 bottom-0 right-0 flex w-full md:w-[480px] p-4 z-50'>
              <div className='flex flex-col bg-white/80 backdrop-blur-3xl rounded-[40px] border border-white/40 shadow-2xl w-full h-full overflow-hidden'>
                <div className='relative z-20 flex items-center justify-between p-8 md:p-10 border-b border-primary/5 bg-white/40 backdrop-blur-md'>
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
