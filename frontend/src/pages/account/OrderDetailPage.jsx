import { Package } from 'lucide-react';
import React from 'react';

export default function OrderDetailPage() {
  return (
    <div className='space-y-8'>
      <div className='text-center'>
        <div className='flex justify-center mb-4'>
          <div className='w-14 h-14 bg-primary/5 rounded-full flex items-center justify-center'>
            <Package className='w-7 h-7 text-primary' />
          </div>
        </div>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Order Details
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          View order information and tracking details
        </p>
      </div>

      <div className='py-20 text-center'>
        <p className='font-serif text-2xl italic text-primary/40'>No order details available.</p>
      </div>
    </div>
  );
}
