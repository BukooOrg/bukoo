import { ChevronLeft, ChevronRight } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';

import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/latest-product-card';
import mockProducts from '@/data/mock/products.json';
import { bookApi, collectionApi } from '@/lib/apiClient';
import { fromApiBooks, reshapeProducts, sortProductsByCover } from '@/lib/sfcc/utils';

const gridVariants = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.03 } },
};

const PAGE_SIZE = 24;

export default function ShopPage() {
  const { collection: collectionHandle } = useParams();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        let collectionId = undefined;
        if (collectionHandle && collectionHandle !== 'joyco-root') {
          const collRes = await collectionApi.findCollections();
          const found = (collRes.data || []).find((c) => c.urlSlug === collectionHandle);
          collectionId = found?.id;
        }

        const bookRes = await bookApi.findBooks({
          status: 'activate',
          search: query || undefined,
          collectionId,
          page,
          pageSize: PAGE_SIZE,
        });
        const items = bookRes.data?.items || [];
        setProducts(fromApiBooks(items).sort(sortProductsByCover));
        setTotalItems(bookRes.data?.pagination?.totalItems || 0);
        setLoading(false);
        return;
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
      setTotalItems(filtered.length);
      const start = (page - 1) * PAGE_SIZE;
      const sorted = [...filtered].sort(sortProductsByCover);
      setProducts(sorted.slice(start, start + PAGE_SIZE));
      setLoading(false);
    }
    loadData();
  }, [collectionHandle, query, page]);

  const totalPages = Math.ceil(totalItems / PAGE_SIZE);

  return (
    <PageLayout>
      <div className='pt-8 pb-24 px-sides max-w-[1440px] mx-auto'>
        {loading ? (
          <div className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12 animate-pulse'>
            {[...Array(12)].map((_, i) => (
              <div key={i} className='aspect-[2/3] bg-gray-100 rounded-2xl' />
            ))}
          </div>
        ) : (
          <>
            {products.length > 0 ? (
              <motion.div
                variants={gridVariants}
                initial='hidden'
                animate='visible'
                className='grid grid-cols-2 lg:grid-cols-4 xl:grid-cols-6 gap-x-6 gap-y-12'>
                {products.map((product) => (
                  <LatestProductCard key={product.id || product.handle} product={product} />
                ))}
              </motion.div>
            ) : (
              <div className='py-32 text-center'>
                <p className='font-sans text-lg font-medium text-gray-500'>
                  No books found matching your criteria.
                </p>
                <Link
                  to='/shop'
                  className='mt-4 inline-block text-[10px] font-black uppercase tracking-widest text-primary hover:underline'>
                  Browse All Collections
                </Link>
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
