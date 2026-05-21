import { ChevronLeft, ChevronRight } from 'lucide-react';
import React, { useState, useEffect } from 'react';

import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/LatestProductCard';
import mockProducts from '@/data/mock/products.json';
import { bookApi } from '@/lib/apiClient';
import { fromApiBooks, reshapeProducts } from '@/lib/sfcc/utils';

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
          setFeaturedProducts(reshaped);
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
      setFeaturedProducts(filtered.slice(start, start + PAGE_SIZE));
      setLoading(false);
    }
    loadData();
  }, [page]);

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  return (
    <PageLayout>
      <div className='pt-8 pb-24 px-sides max-w-[1440px] mx-auto'>
        {loading ? (
          <div className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-pulse'>
            {[...Array(12)].map((_, i) => (
              <div key={i} className='aspect-[2/3] bg-primary/5 rounded-2xl' />
            ))}
          </div>
        ) : (
          <>
            {featuredProducts.length > 0 ? (
              <div className='grid grid-cols-2 duration-700 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-in fade-in'>
                {featuredProducts.map((product) => (
                  <LatestProductCard key={product.id || product.handle} product={product} />
                ))}
              </div>
            ) : (
              <div className='py-32 text-center col-span-full'>
                <p className='font-serif text-2xl italic opacity-30'>
                  Our shelves are being restocked.
                </p>
              </div>
            )}

            {totalPages > 1 && (
              <div className='flex items-center justify-center gap-6 mt-16'>
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className='flex items-center gap-1 px-4 py-2 text-xs font-sans font-bold uppercase tracking-widest text-primary/60 hover:text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors'>
                  <ChevronLeft className='w-4 h-4' />
                  Previous
                </button>
                <span className='text-xs font-sans font-bold text-primary/40'>
                  {page} / {totalPages}
                </span>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className='flex items-center gap-1 px-4 py-2 text-xs font-sans font-bold uppercase tracking-widest text-primary/60 hover:text-primary disabled:opacity-30 disabled:cursor-not-allowed transition-colors'>
                  Next
                  <ChevronRight className='w-4 h-4' />
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </PageLayout>
  );
}
