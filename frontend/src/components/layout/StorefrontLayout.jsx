import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';

import { getCollections } from '@/lib/sfcc';

import { Footer } from './Footer';
import { GenreNav } from './GenreNav';
import { Header } from './header';

export function StorefrontLayout() {
  const location = useLocation();
  const isAccountPage = location.pathname.startsWith('/account');

  const [collections, setCollections] = useState([]);

  useEffect(() => {
    async function load() {
      const data = await getCollections();
      setCollections(data);
    }
    load();
  }, []);

  const activeHandle = location.pathname.startsWith('/shop/')
    ? location.pathname.replace('/shop/', '')
    : null;

  return (
    <div className='flex flex-col min-h-screen font-sans antialiased bg-background text-foreground'>
      <Header />
      {!isAccountPage && (
        <div className='mt-24 md:mt-32'>
          <GenreNav collections={collections} activeHandle={activeHandle} />
        </div>
      )}
      <main className='min-h-screen pt-0'>
        <Outlet />
      </main>
      {!isAccountPage && <Footer />}
      <Toaster closeButton position='bottom-right' />
    </div>
  );
}
