import { Bell } from 'lucide-react';
import React from 'react';

export default function AdminNotificationsPage() {
  return (
    <div className='space-y-8'>
      <div className='text-center pt-8'>
        <h1 className='text-4xl font-serif font-black mb-2 text-primary tracking-tighter'>
          Notifications
        </h1>
        <p className='text-primary/40 font-bold italic text-sm'>View system notifications</p>
      </div>

      <div className='py-20 text-center'>
        <Bell className='w-12 h-12 mx-auto mb-4 text-primary/10' />
        <p className='font-serif text-2xl italic text-primary/40'>No notifications yet.</p>
      </div>
    </div>
  );
}
