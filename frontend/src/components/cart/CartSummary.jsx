import React from 'react';

function formatPrice(amount, currency = 'GBP') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

export function CartSummary({ totalQuantity, totalPrice }) {
  return (
    <div className='bg-card border border-border rounded-lg p-6 space-y-4'>
      <h2 className='font-serif text-xl font-bold text-primary'>Summary</h2>
      <div className='space-y-3 text-sm'>
        <div className='flex justify-between'>
          <span className='text-muted-foreground'>Items</span>
          <span>{totalQuantity}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-muted-foreground'>Subtotal</span>
          <span>{formatPrice(totalPrice)}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-muted-foreground'>Shipping</span>
          <span className='text-muted-foreground'>Calculated at checkout</span>
        </div>
      </div>
      <div className='pt-4 border-t border-border'>
        <div className='flex justify-between items-baseline'>
          <span className='font-serif text-lg font-bold text-primary'>Total</span>
          <span className='font-serif text-2xl font-black text-primary'>
            {formatPrice(totalPrice)}
          </span>
        </div>
      </div>
    </div>
  );
}
