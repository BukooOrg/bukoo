import { BookOpen, Calendar, Globe, Hash, Layers, User } from 'lucide-react';
import { motion } from 'motion/react';
import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

import { AddToCart } from '@/components/cart/AddToCart';
import { PageLayout } from '@/components/layout/PageLayout';
import { ReviewsSection } from '@/components/reviews';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbSeparator,
  BreadcrumbPage,
} from '@/components/ui/navigation/breadcrumb';
import { AddToWishlist } from '@/components/wishlist/AddToWishlist';
import mockProducts from '@/data/mock/products.json';
import { bookApi } from '@/lib/apiClient';
import { fromApiBook } from '@/lib/sfcc/utils';
import { formatPrice, reshapeProduct } from '@/lib/sfcc/utils';

function formatDate(date) {
  if (!date) return '—';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' });
}

export default function ProductDetailPage() {
  const { handle } = useParams();
  const [product, setProduct] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      try {
        const res = await bookApi.viewBookDetail({ bookId: handle, status: 'activate' });
        const reshaped = fromApiBook(res.data);
        if (reshaped) {
          setProduct(reshaped);
          setLoading(false);
          return;
        }
      } catch {
        // API unavailable, fall through
      }

      const mockProduct = mockProducts.find((p) => p.handle === handle || p.id === handle);
      setProduct(mockProduct ? reshapeProduct(mockProduct) : null);
      setLoading(false);
    }
    loadData();
  }, [handle]);

  if (loading) {
    return (
      <PageLayout>
        <div className='pt-48 text-lg italic text-center opacity-50'>Opening the pages...</div>
      </PageLayout>
    );
  }

  if (!product) {
    return (
      <PageLayout>
        <div className='pt-48 text-3xl text-center'>Book not found.</div>
      </PageLayout>
    );
  }

  const price = product.priceRange?.minVariantPrice?.amount || '0';
  const currency = product.priceRange?.minVariantPrice?.currencyCode || 'MYR';

  return (
    <PageLayout>
      <div className='px-sides max-w-6xl mx-auto pt-24 pb-24 md:pt-32 text-black'>
        {/* Breadcrumb */}
        <Breadcrumb className='mb-6'>
          <BreadcrumbList>
            <BreadcrumbItem>
              <BreadcrumbLink asChild className='text-gray-600 hover:text-black'>
                <Link to='/shop'>Shop</Link>
              </BreadcrumbLink>
            </BreadcrumbItem>
            <BreadcrumbSeparator />
            <BreadcrumbItem>
              <BreadcrumbPage className='text-gray-900'>{product.title}</BreadcrumbPage>
            </BreadcrumbItem>
          </BreadcrumbList>
        </Breadcrumb>

        {/* Hero — cover + info */}
        <div className='flex flex-col gap-8 md:flex-row md:gap-12'>
          {/* Cover image */}
          <div className='shrink-0 w-64 mx-auto md:w-80 md:mx-0'>
            <div className='overflow-hidden rounded-2xl shadow-xl aspect-[2/3] bg-gray-100'>
              {product.featuredImage?.url ? (
                <motion.img
                  src={product.featuredImage.url}
                  alt={product.title}
                  referrerpolicy='no-referrer'
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.5 }}
                  className='object-contain w-full h-full'
                />
              ) : (
                <div className='flex items-center justify-center w-full h-full'>
                  <BookOpen className='w-20 h-20 text-gray-300' />
                </div>
              )}
            </div>
          </div>

          {/* Book info */}
          <div className='flex-1'>
            {/* Title & author */}
            <div className='mb-6'>
              <h1 className='text-4xl font-bold tracking-tight md:text-5xl'>{product.title}</h1>
              <p className='mt-1 text-lg text-gray-500'>{product.vendor || 'Bukoo Editions'}</p>
            </div>

            {/* Tags */}
            {product.tags?.length > 0 && (
              <div className='flex flex-wrap gap-2 mb-6'>
                {product.tags.map((tag) => (
                  <span
                    key={tag}
                    className='px-4 py-2 text-sm font-medium rounded-full bg-gray-100 text-gray-600'>
                    {tag}
                  </span>
                ))}
              </div>
            )}

            {/* Description */}
            <h2 className='text-sm font-bold uppercase tracking-[0.2em] text-gray-500 mb-3'>
              About This Book
            </h2>
            <p className='mb-8 text-base leading-relaxed text-gray-600'>
              {product.description || 'No description available.'}
            </p>

            {/* Metadata */}
            <div className='grid grid-cols-2 gap-4 p-6 mb-8 bg-white border border-gray-200 rounded-2xl md:grid-cols-3'>
              <div className='flex flex-col gap-1.5'>
                <div className='flex items-center gap-2 text-gray-400'>
                  <Hash className='w-4 h-4' />
                  <span className='text-sm font-medium'>ISBN</span>
                </div>
                <p className='text-base text-black'>{product.isbn || '—'}</p>
              </div>
              <div className='flex flex-col gap-1.5'>
                <div className='flex items-center gap-2 text-gray-400'>
                  <Layers className='w-4 h-4' />
                  <span className='text-sm font-medium'>Pages</span>
                </div>
                <p className='text-base text-black'>{product.pageCount || '—'}</p>
              </div>
              <div className='flex flex-col gap-1.5'>
                <div className='flex items-center gap-2 text-gray-400'>
                  <Globe className='w-4 h-4' />
                  <span className='text-sm font-medium'>Language</span>
                </div>
                <p className='text-base text-black'>{product.language || '—'}</p>
              </div>
              <div className='flex flex-col gap-1.5'>
                <div className='flex items-center gap-2 text-gray-400'>
                  <User className='w-4 h-4' />
                  <span className='text-sm font-medium'>Publisher</span>
                </div>
                <p className='text-base text-black'>
                  {product.publisher?.name || product.vendor || '—'}
                </p>
              </div>
              <div className='flex flex-col gap-1.5'>
                <div className='flex items-center gap-2 text-gray-400'>
                  <Calendar className='w-4 h-4' />
                  <span className='text-sm font-medium'>Published</span>
                </div>
                <p className='text-base text-black'>{formatDate(product.publishedDate)}</p>
              </div>
            </div>

            {/* Price & CTA */}
            <div className='flex items-center gap-3 p-6 border border-gray-200 rounded-2xl bg-white'>
              <div className='flex-1'>
                <p className='text-sm font-medium uppercase text-gray-500'>Price</p>
                <p className='text-3xl font-bold text-black'>{formatPrice(price, currency)}</p>
              </div>
              <AddToCart
                bookId={product.id}
                available={true}
                className='flex-1 h-14 bg-black text-white text-base font-medium rounded-lg hover:bg-white hover:text-black'
              />
              <AddToWishlist
                bookId={product.id}
                size='lg'
                className='bg-black text-white hover:bg-white hover:text-black'
              />
            </div>
          </div>
        </div>

        {/* Reviews section */}
        <ReviewsSection bookId={product.id} />
      </div>
    </PageLayout>
  );
}
