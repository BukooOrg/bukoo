import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

export function AdminLayout() {
  return (
    <div className='flex min-h-screen font-sans antialiased bg-background text-foreground'>
      <aside className='flex flex-col w-64 gap-2 p-6 border-r shrink-0 border-border bg-white/50'>
        <p className='mb-4 text-xs font-black tracking-widest uppercase text-primary/40'>Admin</p>
        <div className='text-sm italic text-primary/40'>Navigation coming soon</div>
      </aside>
      <div className='flex flex-col flex-1'>
        <header className='flex items-center h-16 px-6 border-b border-border'>
          <p className='text-xs font-black tracking-widest uppercase text-primary/40'>
            Bukoo Admin
          </p>
        </header>
        <main className='flex-1 p-6'>
          <Outlet />
        </main>
      </div>
      <Toaster closeButton position='bottom-right' />
    </div>
  );
}
