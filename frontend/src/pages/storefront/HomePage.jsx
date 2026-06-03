import { ChevronLeft, ChevronRight } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';

import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/latest-product-card';
import { HeroSection } from '@/components/storefront/HeroSection';
import mockProducts from '@/data/mock/products.json';
import { bookApi } from '@/lib/apiClient';
import { fromApiBooks, reshapeProducts, sortProductsByCover } from '@/lib/sfcc/utils';

const gridVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.03 } },
};

const PAGE_SIZE = 24;

export default function HomePage() {
  const [featuredProducts, setFeaturedProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  useEffect(() => {
    async function loadData() {
      try {
        const bookRes = await bookApi.findBooks({
          status: 'activate',
          page,
          pageSize: PAGE_SIZE,
        });
        const items = bookRes.data?.items || [];
        const reshaped = fromApiBooks(items);
        if (reshaped.length > 0) {
          setFeaturedProducts(reshaped.sort(sortProductsByCover));
          setTotalItems(bookRes.data?.pagination?.totalItems || 0);
          setLoading(false);
          return;
        }
      } catch {
        // API unavailable, fall through to mock
      }

      const filtered = reshapeProducts(mockProducts);
      setTotalItems(filtered.length);
      const start = (page - 1) * PAGE_SIZE;
      const sorted = [...filtered].sort(sortProductsByCover);
      setFeaturedProducts(sorted.slice(start, start + PAGE_SIZE));
      setLoading(false);
    }
    loadData();
  }, [page]);

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  return (
    <PageLayout>
      <HeroSection />

      <div className='pt-8 pb-24 px-sides max-w-[1440px] mx-auto'>
        {loading ? (
          <div className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-pulse'>
            {[...Array(12)].map((_, i) => (
              <div key={i} className='aspect-[2/3] bg-gray-100 rounded-2xl' />
            ))}
          </div>
        ) : (
          <>
            {featuredProducts.length > 0 ? (
              <motion.div
                variants={gridVariants}
                initial='hidden'
                animate='visible'
                className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12'>
                {featuredProducts.map((product) => (
                  <LatestProductCard key={product.id || product.handle} product={product} />
                ))}
              </motion.div>
            ) : (
              <div className='py-32 text-center col-span-full'>
                <p className='font-sans text-lg font-medium text-gray-500'>
                  Our shelves are being restocked.
                </p>
              </div>
            )}

            {totalPages > 1 && (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.2, delay: 0.15 }}
                className='flex items-center justify-center gap-6 mt-16'>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className='flex items-center gap-1 px-4 py-2 text-xs font-sans font-bold uppercase tracking-widest text-gray-500 hover:text-black disabled:opacity-30 disabled:cursor-not-allowed transition-colors'>
                  <ChevronLeft className='w-4 h-4' />
                  Previous
                </button>
                <span className='text-xs font-sans font-bold text-gray-400'>
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className='flex items-center gap-1 px-4 py-2 text-xs font-sans font-bold uppercase tracking-widest text-gray-500 hover:text-black disabled:opacity-30 disabled:cursor-not-allowed transition-colors'>
                  Next
                  <ChevronRight className='w-4 h-4' />
                </button>
              </motion.div>
            )}
          </>
        )}
      </div>
    </PageLayout>
  );
}
