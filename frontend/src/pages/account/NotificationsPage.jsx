import React from 'react';

export default function NotificationsPage() {
  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Notifications
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>
          Manage your notification preferences
        </p>
      </div>

      <div className='py-20 text-center'>
        <p className='font-serif text-2xl italic text-primary/40'>
          No notifications. We'll keep you updated here.
        </p>
      </div>
    </div>
  );
}
