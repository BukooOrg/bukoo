import { LayoutDashboard } from 'lucide-react';
import React from 'react';

export default function AdminDashboardPage() {
  return (
    <div className='space-y-8 max-w-6xl'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Dashboard
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>Welcome to the admin panel</p>
      </div>

      <div className='py-20 text-center'>
        <LayoutDashboard className='w-12 h-12 mx-auto mb-4 text-primary/10' />
        <p className='font-serif text-2xl italic text-primary/40'>Admin dashboard coming soon.</p>
      </div>
    </div>
  );
}
