import React, { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';

import { useCart } from '@/components/cart/CartContext';
import { OrderStatusBadge } from '@/components/orders/OrderStatusBadge';
import { Spinner } from '@/components/ui/feedback/spinner';
import { Button } from '@/components/ui/forms/button';
import { orderApi } from '@/lib/apiClient';

function formatDate(dateValue) {
  if (!dateValue) return '';
  const d = typeof dateValue === 'string' ? new Date(dateValue) : dateValue;
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

function ConfirmationItem({ item }) {
  return (
    <div className='flex gap-4 py-3 border-b border-primary/5 last:border-0'>
      <div className='w-12 h-16 shrink-0 overflow-hidden rounded bg-primary/5'>
        {item.bookCoverUrl ? (
          <img
            src={item.bookCoverUrl}
            alt={item.bookTitle}
            className='w-full h-full object-cover'
          />
        ) : (
          <div className='w-full h-full flex items-center justify-center text-primary/40 text-xs'>
            No cover
          </div>
        )}
      </div>
      <div className='flex-1 min-w-0'>
        <p className='text-base font-medium truncate'>{item.bookTitle}</p>
        <p className='text-sm text-primary/40'>
          RM {Number(item.unitPrice).toFixed(2)} &middot; Qty: {item.quantity}
        </p>
      </div>
      <p className='text-base font-medium shrink-0'>RM {Number(item.lineTotal).toFixed(2)}</p>
    </div>
  );
}

export default function CheckoutConfirmationPage() {
  const [searchParams] = useSearchParams();
  const orderId = searchParams.get('orderId');
  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const { refreshCart } = useCart();

  useEffect(() => {
    async function loadOrder() {
      if (!orderId) {
        setLoading(false);
        return;
      }
      try {
        const response = await orderApi.viewOrderDetail({ orderId });
        setOrder(response.data);
        await refreshCart();
      } catch {
        // Order not found
      } finally {
        setLoading(false);
      }
    }
    loadOrder();
  }, [orderId, refreshCart]);

  if (loading) {
    return (
      <div className='flex items-center justify-center min-h-[60vh]'>
        <Spinner size='lg' />
      </div>
    );
  }

  if (!orderId || !order) {
    return (
      <div className='px-sides py-24'>
        <div className='max-w-2xl mx-auto text-center'>
          <h1 className='font-serif text-4xl font-black text-primary'>Order Not Found</h1>
          <Link to='/shop' className='mt-4 text-primary underline'>
            Continue Shopping
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className='px-sides py-16'>
      <div className='max-w-2xl mx-auto'>
        <div className='text-center mb-8'>
          <div className='inline-flex items-center justify-center w-16 h-16 rounded-full bg-primary/10 mb-4'>
            <svg
              className='w-8 h-8 text-primary'
              fill='none'
              viewBox='0 0 24 24'
              stroke='currentColor'>
              <path
                strokeLinecap='round'
                strokeLinejoin='round'
                strokeWidth={2}
                d='M5 13l4 4L19 7'
              />
            </svg>
          </div>
          <h1 className='font-serif text-4xl font-black text-primary tracking-tighter'>
            Order Confirmed
          </h1>
          <p className='mt-2 text-primary/40'>
            Order #{order.id.slice(0, 8)} &middot; {formatDate(order.createdAt)}
          </p>
          <OrderStatusBadge status={order.status} className='mt-3' />
        </div>

        <div className='bg-white border border-primary/5 rounded-lg p-6 space-y-4'>
          <h2 className='text-lg font-bold text-primary'>Order Items ({order.items.length})</h2>
          {order.items.map((item) => (
            <ConfirmationItem key={item.id} item={item} />
          ))}

          <div className='pt-4 space-y-2'>
            <div className='flex justify-between text-sm'>
              <span className='text-primary/40'>Subtotal</span>
              <span>RM {Number(order.subtotal).toFixed(2)}</span>
            </div>
            <div className='flex justify-between text-sm'>
              <span className='text-primary/40'>Shipping</span>
              <span>RM {Number(order.shippingCost).toFixed(2)}</span>
            </div>
            <div className='flex justify-between text-lg font-bold pt-2 border-t'>
              <span>Total</span>
              <span>RM {Number(order.total).toFixed(2)}</span>
            </div>
          </div>
        </div>

        <div className='flex gap-3 mt-6'>
          <Link to={`/account/orders/${order.id}`} className='flex-1'>
            <Button className='w-full bg-primary text-secondary h-14 text-lg' size='lg'>
              View Order
            </Button>
          </Link>
          <Link to='/shop' className='flex-1'>
            <Button variant='outline' className='w-full h-14 text-lg' size='lg'>
              Continue Shopping
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
