import React, { useState, useEffect } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import { Toaster } from 'sonner';

import { SkipLink } from '@/components/ui/misc/skip-link';
import { getCollections } from '@/lib/sfcc';

import { Footer } from './Footer';
import { GenreNav } from './GenreNav';
import { Header } from './header';

export function StorefrontLayout({ customHeader = null }) {
  const location = useLocation();
  const isAccountPage = location.pathname.startsWith('/account');
  const showGenreNav = location.pathname === '/' || location.pathname.startsWith('/shop');

  const [collections, setCollections] = useState([]);

  useEffect(() => {
    if (showGenreNav) {
      async function load() {
        const data = await getCollections();
        setCollections(data);
      }
      load();
    }
  }, [showGenreNav]);

  const activeHandle = location.pathname.startsWith('/shop/')
    ? location.pathname.replace('/shop/', '')
    : null;

  return (
    <div className='flex flex-col min-h-screen font-sans antialiased bg-background text-foreground'>
      <SkipLink />
      {customHeader ?? <Header />}
      <div className='mt-24 md:mt-32'>
        {showGenreNav && <GenreNav collections={collections} activeHandle={activeHandle} />}
        <main id='main-content' className='min-h-screen pt-0'>
          <Outlet />
        </main>
      </div>
      {!isAccountPage && <Footer />}
      <Toaster closeButton position='bottom-right' />
    </div>
  );
}
