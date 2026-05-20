import React from 'react';
import { Link } from 'react-router-dom';

import { DeleteItemButton } from './DeleteItemButton';
import { EditItemQuantityButton } from './EditItemQuantityButton';

function formatPrice(amount, currency = 'GBP') {
  return `${currency} ${Number(amount).toFixed(2)}`;
}

export function CartItemCard({ item }) {
  const subtotal = (Number(item.book.price) * item.quantity).toFixed(2);

  return (
    <div className='bg-card border border-border rounded-lg p-4'>
      <div className='flex gap-4'>
        <div className='relative w-24 h-32 shrink-0 overflow-hidden rounded-sm bg-muted'>
          {item.book.coverUrl ? (
            <img
              src={item.book.coverUrl}
              alt={item.book.title}
              className='w-full h-full object-cover'
            />
          ) : (
            <div className='w-full h-full flex items-center justify-center text-muted-foreground text-xs'>
              No cover
            </div>
          )}
        </div>

        <div className='flex flex-col flex-1 min-w-0'>
          <Link
            to={`/product/${item.bookId}`}
            className='font-serif text-lg font-semibold text-primary hover:underline truncate'>
            {item.book.title}
          </Link>

          <p className='text-sm text-muted-foreground mt-1'>{formatPrice(item.book.price)} each</p>

          <div className='flex items-center justify-between mt-auto pt-3'>
            <div className='flex items-center h-8 rounded-md border border-border'>
              <EditItemQuantityButton item={item} type='minus' />
              <span className='w-8 text-center text-sm'>{item.quantity}</span>
              <EditItemQuantityButton item={item} type='plus' />
            </div>

            <div className='flex items-center gap-4'>
              <span className='font-semibold text-primary'>{formatPrice(subtotal)}</span>
              <DeleteItemButton item={item} />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
