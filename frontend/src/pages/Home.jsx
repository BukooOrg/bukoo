import React, { useState, useEffect } from 'react';

import { PageLayout } from '@/components/layout/page-layout';
import { LatestProductCard } from '@/components/products/latest-product-card';
import { getCollectionProducts, getCollections } from '@/lib/sfcc';

export default function Home() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [_collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

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
      <div className='pt-36 pb-24 px-sides max-w-[1440px] mx-auto'>
        {/* Results Info (Minimalist) */}
        <div className='flex items-center justify-between pb-6 mb-10 border-b border-border'>
          <p className='text-[10px] font-sans font-black uppercase tracking-[0.3em] text-primary'>
            Featured Selection
          </p>
          <div className='flex gap-4 text-[10px] font-sans font-black uppercase tracking-widest text-primary/60'>
            <span>{featuredProducts.length} Results</span>
          </div>
        </div>

        {/* Product Grid */}
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
