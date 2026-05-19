import React from 'react';

export default function OrdersPage() {
  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Orders
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          View your order history and track deliveries
        </p>
      </div>

      <div className='py-20 text-center'>
        <p className='font-serif text-2xl italic text-primary/40'>
          No orders yet. Start shopping to see your orders here.
        </p>
      </div>
    </div>
  );
}
