import { ResponseError } from '@bukoo/api-client';
import React, { useState, useEffect } from 'react';

import { GenreNav } from '@/components/layout/GenreNav';
import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/LatestProductCard';
import { healthApi, userApi } from '@/lib/apiClient';
import { getCollectionProducts, getCollections } from '@/lib/sfcc';

export default function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function healthCheck() {
      try {
        const res = await healthApi.healthCheck();
        console.log(res);
      } catch (err) {
        if (err instanceof ResponseError) {
          const body = await err.response.json();
          console.error(body);
        }
      }
    }
    healthCheck();
  }, []);

  useEffect(() => {
    async function getMe() {
      try {
        const res = await userApi.getMe();
        console.log(res);
      } catch (err) {
        if (err instanceof ResponseError) {
          const body = await err.response.json();
          console.error(body);
        }
      }
    }
    getMe();
  }, []);

  useEffect(() => {
    async function loadData() {
      try {
        const [products, cols] = await Promise.all([
          getCollectionProducts({ collection: 'joyco-root' }),
          getCollections(),
        ]);
        setFeaturedProducts(products);
        setCollections(cols);
      } catch (error) {
        console.error('Failed to load home page data', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  return (
    <PageLayout>
      <div className='pt-0 pb-24 px-sides max-w-[1440px] mx-auto'>
        <GenreNav collections={collections} />

        <div className='flex items-center justify-between pb-6 mb-10 border-b border-border mt-6'>
          <p className='text-[10px] font-sans font-black uppercase tracking-[0.3em] text-primary'>
            Featured Selection
          </p>
          <div className='flex gap-4 text-[10px] font-sans font-black uppercase tracking-widest text-primary/60'>
            <span>{featuredProducts.length} Results</span>
          </div>
        </div>

        {loading ? (
          <div className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-pulse'>
            {[...Array(12)].map((_, i) => (
              <div key={i} className='aspect-[2/3] bg-primary/5 rounded-2xl' />
            ))}
          </div>
        ) : (
          <div className='grid grid-cols-2 duration-700 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-in fade-in'>
            {featuredProducts.length > 0 ? (
              featuredProducts.map((product) => (
                <LatestProductCard key={product.id || product.handle} product={product} />
              ))
            ) : (
              <div className='py-32 text-center col-span-full'>
                <p className='font-serif text-2xl italic opacity-30'>
                  Our shelves are being restocked.
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
