import React from 'react';

function formatPrice(amount, currency = 'RM') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

export function CartSummary({ totalQuantity, totalPrice }) {
  return (
    <div className='bg-white border border-primary/5 rounded-lg p-8 space-y-6'>
      <h2 className='font-serif text-2xl font-bold text-primary'>Summary</h2>
      <div className='space-y-4 text-base'>
        <div className='flex justify-between'>
          <span className='text-primary/40'>Items</span>
          <span>{totalQuantity}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-primary/40'>Subtotal</span>
          <span>{formatPrice(totalPrice)}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-primary/40'>Shipping</span>
          <span className='text-primary/40'>Calculated at checkout</span>
        </div>
      </div>
      <div className='pt-6 border-t border-primary/5'>
        <div className='flex justify-between items-baseline'>
          <span className='font-serif text-xl font-bold text-primary'>Total</span>
          <span className='font-serif text-3xl font-black text-primary'>
            {formatPrice(totalPrice)}
          </span>
        </div>
      </div>
    </div>
  );
}
