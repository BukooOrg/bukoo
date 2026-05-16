import React from 'react';
import { Outlet } from 'react-router-dom';
import { Toaster } from 'sonner';

import { Footer } from './Footer';
import { Header } from './header';

export function StorefrontLayout() {
  return (
    <div className='flex flex-col min-h-screen font-sans antialiased bg-background text-foreground'>
      <Header />
      <main className='min-h-screen pt-28 md:pt-40'>
        <Outlet />
      </main>
      <Footer />
      <Toaster closeButton position='bottom-right' />
    </div>
  );
}
