import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';

import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/LatestProductCard';
import mockProducts from '@/data/mock/products.json';
import { bookApi } from '@/lib/apiClient';
import { fromApiBooks, reshapeProducts } from '@/lib/sfcc/utils';

export default function ShopPage() {
  const { collection: collectionHandle } = useParams();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const bookRes = await bookApi.findBooks({
          status: 'activate',
          search: query || undefined,
          pageSize: 48,
        });
        const reshaped = fromApiBooks(bookRes.data?.items || []);
        if (reshaped.length > 0) {
          setProducts(reshaped);
          setLoading(false);
          return;
        }
      } catch {
        // API unavailable, fall through
      }

      let filtered = reshapeProducts(mockProducts);
      if (collectionHandle && collectionHandle !== 'joyco-root') {
        filtered = filtered.filter((p) => p.categoryId === collectionHandle);
      }
      if (query) {
        const q = query.toLowerCase();
        filtered = filtered.filter((p) => p.title.toLowerCase().includes(q));
      }
      setProducts(filtered);
      setLoading(false);
    }
    loadData();
  }, [collectionHandle, query]);

  return (
    <PageLayout>
      <div className='pt-8 pb-24 px-sides max-w-[1440px] mx-auto'>
        <div className='flex items-center justify-between pb-6 mb-10 border-b border-border'>
          <p className='text-[10px] font-sans font-black uppercase tracking-[0.3em] text-primary'>
            {products.length} Results
          </p>
          <div className='flex gap-4 text-[10px] font-sans font-black uppercase tracking-widest text-primary/60'>
            <span>Sort by: Newest</span>
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
            {products.length > 0 ? (
              products.map((product) => (
                <LatestProductCard key={product.id || product.handle} product={product} />
              ))
            ) : (
              <div className='py-32 text-center col-span-full'>
                <p className='font-serif text-2xl italic opacity-30'>
                  No books found matching your criteria.
                </p>
                <Link
                  to='/shop'
                  className='mt-4 inline-block text-[10px] font-black uppercase tracking-widest text-primary hover:underline'>
                  Browse All Collections
                </Link>
              </div>
            )}
          </div>
        )}
      </div>
    </PageLayout>
  );
}
