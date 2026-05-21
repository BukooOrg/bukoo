import React from 'react';

function formatPrice(amount, currency = 'RM') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

export function CartSummary({ totalQuantity, totalPrice }) {
  return (
    <div className='bg-white border border-gray-200 rounded-lg p-8 space-y-6'>
      <h2 className='font-serif text-2xl font-bold text-black'>Summary</h2>
      <div className='space-y-4 text-base'>
        <div className='flex justify-between'>
          <span className='text-gray-500'>Items</span>
          <span>{totalQuantity}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-gray-500'>Subtotal</span>
          <span>{formatPrice(totalPrice)}</span>
        </div>
        <div className='flex justify-between'>
          <span className='text-gray-500'>Shipping</span>
          <span className='text-gray-500'>Calculated at checkout</span>
        </div>
      </div>
      <div className='pt-6 border-t border-gray-200'>
        <div className='flex justify-between items-baseline'>
          <span className='font-serif text-xl font-bold text-black'>Total</span>
          <span className='font-serif text-3xl font-black text-black'>
            {formatPrice(totalPrice)}
          </span>
        </div>
      </div>
    </div>
  );
}
