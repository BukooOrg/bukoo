import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';

import { PageLayout } from '@/components/layout/PageLayout';
import { LatestProductCard } from '@/components/products/LatestProductCard';
import { getCollectionProducts, getCollections } from '@/lib/sfcc';

export default function Shop() {
  const { collection: collectionHandle } = useParams();
  const [searchParams] = useSearchParams();
  const query = searchParams.get('q') || '';

  const [products, setProducts] = useState([]);
  const [_collections, setCollections] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const [prodData, collData] = await Promise.all([
          getCollectionProducts({
            collection: collectionHandle || 'joyco-root',
            query,
          }),
          getCollections(),
        ]);
        setProducts(prodData);
        setCollections(collData);
      } catch (error) {
        console.error('Failed to load shop data', error);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [collectionHandle, query]);

  // const currentCollection = collections.find(
  //   (c) => c.handle === (collectionHandle || 'joyco-root')
  // );

  return (
    <PageLayout>
      <div className='pt-36 pb-24 px-sides max-w-[1440px] mx-auto'>
        {/* Results Info (Minimalist) */}
        <div className='flex items-center justify-between pb-6 mb-10 border-b border-border'>
          <p className='text-[10px] font-sans font-black uppercase tracking-[0.3em] text-primary'>
            {products.length} Results
          </p>
          <div className='flex gap-4 text-[10px] font-sans font-black uppercase tracking-widest text-primary/60'>
            <span>Sort by: Newest</span>
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
