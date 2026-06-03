'use client';

import { ArrowRight, PlusCircleIcon, ShoppingBag, X } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link, useLocation, useNavigate } from 'react-router-dom';

import { Button } from '../ui/forms/button';

import { useCart } from './CartContext';
import { ConfirmDialog } from './ConfirmDialog';

function formatPrice(amount, currency = 'RM') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

const CartItems = ({ closeCart }) => {
  const { cart, removeFromCart, updateQuantity } = useCart();
  const navigate = useNavigate();
  const [pendingRemove, setPendingRemove] = useState(null);
  const [removing, setRemoving] = useState(false);

  if (!cart) return <></>;

  const handleCheckout = (e) => {
    e.preventDefault();
    closeCart();
    navigate('/checkout');
  };

  const handleRemove = async () => {
    if (!pendingRemove) return;
    setRemoving(true);
    try {
      await removeFromCart(pendingRemove.id);
    } catch {
      console.error('Failed to remove item');
    } finally {
      setRemoving(false);
      setPendingRemove(null);
    }
  };

  const handleQuantityChange = async (itemId, itemTitle, newQuantity) => {
    if (newQuantity <= 0) {
      const item = cart.items.find((i) => i.id === itemId);
      if (item) setPendingRemove({ id: itemId, title: item.book.title });
      return;
    }
    try {
      await updateQuantity(itemId, newQuantity);
    } catch {
      console.error('Failed to update quantity');
    }
  };

  return (
    <div className='flex flex-col h-full'>
      <div className='flex justify-between px-1 text-base text-primary/40'>
        <span>Products</span>
        <span>{cart.items.length} items</span>
      </div>
      <div className='flex-1 py-6 space-y-6 overflow-auto'>
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
                  onRemove={(itemId) => {
                    const item = cart.items.find((i) => i.id === itemId);
                    if (item) setPendingRemove({ id: itemId, title: item.book.title });
                  }}
                  onQuantityChange={handleQuantityChange}
                  onCloseCart={closeCart}
                />
              </motion.div>
            ))}
        </AnimatePresence>
      </div>
      <div className='py-6 text-base text-primary/60 space-y-4'>
        <div className='flex items-center justify-between pt-3 border-t border-primary/5'>
          <p>Shipping</p>
          <p className='text-right'>Calculated at checkout</p>
        </div>
        <div className='flex items-center justify-between'>
          <p className='text-lg font-medium text-primary'>Total</p>
          <p className='text-2xl font-bold text-primary'>{formatPrice(cart.totalPrice)}</p>
        </div>
      </div>
      <Button
        onClick={handleCheckout}
        size='lg'
        className='relative flex items-center justify-between w-full gap-3 bg-primary text-secondary h-14 text-lg'>
        Proceed to Checkout
        <ArrowRight className='size-6' />
      </Button>

      <ConfirmDialog
        open={!!pendingRemove}
        onOpenChange={(open) => !open && setPendingRemove(null)}
        title='Remove from cart?'
        description={
          pendingRemove ? `This will remove "${pendingRemove.title}" from your cart.` : ''
        }
        onConfirm={handleRemove}
        loading={removing}
      />
    </div>
  );
};

function CartItemRow({ item, onRemove, onQuantityChange, onCloseCart }) {
  const subtotal = (Number(item.book.price) * item.quantity).toFixed(2);

  return (
    <div className='flex gap-5 p-5 border border-primary/5 rounded-2xl bg-white'>
      <div className='w-24 h-36 overflow-hidden rounded-2xl bg-primary/5 shrink-0'>
        {item.book.coverUrl ? (
          <img
            src={item.book.coverUrl}
            alt={item.book.title}
            className='w-full h-full object-cover'
          />
        ) : (
          <div className='w-full h-full flex items-center justify-center text-primary/40 text-sm'>
            No cover
          </div>
        )}
      </div>
      <div className='flex flex-col flex-1 min-w-0'>
        <Link
          to={`/product/${item.bookId}`}
          onClick={onCloseCart}
          className='text-lg font-medium font-serif hover:underline truncate'>
          {item.book.title}
        </Link>
        <p className='text-base text-primary/40 mt-1'>RM {item.book.price} each</p>
        <div className='flex items-center justify-between mt-4'>
          <div className='flex h-10 items-center border border-primary/5 rounded-2xl'>
            <QuantityButton
              onClick={() => onQuantityChange(item.id, item.book.title, item.quantity - 1)}
              type='minus'
            />
            <span className='w-10 text-center text-base'>{item.quantity}</span>
            <QuantityButton
              onClick={() => onQuantityChange(item.id, item.book.title, item.quantity + 1)}
              type='plus'
            />
          </div>
          <div className='flex items-center gap-4'>
            <span className='text-lg font-medium'>RM {subtotal}</span>
            <button
              onClick={() => onRemove(item.id)}
              className='text-sm text-primary/40 hover:text-destructive'
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
      className='flex items-center justify-center w-10 h-full hover:bg-primary/5 transition-colors'>
      {type === 'plus' ? <PlusCircleIcon className='size-5' /> : <MinusIcon className='size-5' />}
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
  const { cart, justAdded, clearJustAdded } = useCart();
  const [isOpen, setIsOpen] = useState(false);
  const openCart = () => setIsOpen(true);
  const closeCart = () => setIsOpen(false);
  const { pathname } = useLocation();

  useEffect(() => {
    if (justAdded && !isOpen) {
      setIsOpen(true);
      clearJustAdded();
    }
  }, [justAdded, isOpen, clearJustAdded]);

  useEffect(() => {
    if (pathname === '/checkout') closeCart();
  }, [pathname]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  const renderCartContent = () => {
    if (!cart || !cart.items || cart.items.length === 0) {
      return (
        <div className='flex flex-col items-center justify-center h-full text-center'>
          <ShoppingBag className='size-16 text-primary/30 mb-6' />
          <p className='text-xl font-medium text-primary/60'>Your cart is empty</p>
          <Link
            to='/shop'
            onClick={closeCart}
            className='mt-6 text-base font-medium text-primary underline'>
            Continue Shopping
          </Link>
        </div>
      );
    }

    return <CartItems closeCart={closeCart} />;
  };

  return (
    <>
      <Button
        aria-label='Open cart'
        onClick={openCart}
        variant='ghost'
        size='icon'
        className='relative transition-colors text-primary hover:bg-primary/5'>
        <ShoppingBag className='size-5' />
        {(cart?.totalQuantity || 0) > 0 && (
          <span className='absolute -top-1 -right-1 size-4 flex items-center justify-center text-[9px] font-bold bg-primary text-secondary rounded-full'>
            {cart.totalQuantity}
          </span>
        )}
      </Button>
      {isOpen &&
        createPortal(
          <AnimatePresence>
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.2 }}
                className='fixed inset-0 z-[9999] bg-primary/40'
                onClick={closeCart}
                aria-hidden='true'
              />

              <motion.div
                initial={{ x: '100%' }}
                animate={{ x: 0 }}
                exit={{ x: '100%' }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className='fixed top-0 right-0 bottom-0 z-[9999] w-full max-w-lg bg-white shadow-xl'>
                <div className='flex flex-col h-full'>
                  <div className='flex items-center justify-between p-8 border-b border-primary/5'>
                    <h2 className='text-2xl font-bold font-serif text-primary'>Your Cart</h2>
                    <div className='flex items-center gap-3'>
                      <Link
                        to='/account/cart'
                        onClick={closeCart}
                        className='text-sm font-medium text-primary/40 hover:text-primary underline'>
                        View full cart
                      </Link>
                      <Button
                        size='icon'
                        variant='ghost'
                        aria-label='Close cart'
                        onClick={closeCart}
                        className='text-primary/40 hover:text-primary'>
                        <X className='size-6' />
                      </Button>
                    </div>
                  </div>

                  <div className='flex-1 p-8 overflow-hidden'>{renderCartContent()}</div>
                </div>
              </motion.div>
            </>
          </AnimatePresence>,
          document.body
        )}
    </>
  );
}
