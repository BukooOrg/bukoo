import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';

import { useCart } from '@/components/cart/CartContext';
import { CartItemCard } from '@/components/cart/CartItemCard';
import { CartSummary } from '@/components/cart/CartSummary';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';

export default function CartPage() {
  const { cart, loading, clearCart } = useCart();
  const [clearing, setClearing] = useState(false);

  const handleClearAll = async () => {
    if (!confirm('Remove all items from cart?')) return;
    setClearing(true);
    try {
      await clearCart();
      toast.success('Cart cleared');
    } catch {
      toast.error('Failed to clear cart');
    } finally {
      setClearing(false);
    }
  };

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (cart.items.length === 0) {
    return (
      <div className='px-sides py-16'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black text-primary tracking-tighter'>
            Your Bag is Empty
          </h1>
          <p className='mt-4 text-muted-foreground'>
            Find your next favorite story and add it to your bag.
          </p>
          <Link to='/shop'>
            <Button className='mt-8 bg-primary text-secondary' size='lg'>
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className='px-sides py-12'>
      <div className='max-w-6xl mx-auto'>
        <div className='flex items-center justify-between mb-8'>
          <h1 className='font-serif text-4xl font-black text-primary tracking-tighter'>Your Bag</h1>
          <Button variant='outline' size='sm' onClick={handleClearAll} disabled={clearing}>
            {clearing ? 'Clearing...' : 'Clear All'}
          </Button>
        </div>

        <div className='grid grid-cols-1 lg:grid-cols-3 gap-8'>
          <div className='lg:col-span-2 space-y-4'>
            {cart.items
              .sort((a, b) => a.book.title.localeCompare(b.book.title))
              .map((item) => (
                <CartItemCard key={item.id} item={item} />
              ))}
          </div>

          <div className='lg:col-span-1'>
            <div className='sticky top-24'>
              <CartSummary totalQuantity={cart.totalQuantity} totalPrice={cart.totalPrice} />
              <div className='mt-4 space-y-3'>
                <Link to='/checkout'>
                  <Button className='w-full bg-primary text-secondary' size='lg'>
                    Proceed to Checkout
                  </Button>
                </Link>
                <Link to='/shop'>
                  <Button variant='outline' className='w-full' size='lg'>
                    Continue Shopping
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
