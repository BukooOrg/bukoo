import { Suspense } from 'react';
import { Link } from 'react-router-dom';

import { formatPrice } from '@/lib/sfcc/utils';
import { cn } from '@/lib/utils';

import { AddToCart } from '../cart/AddToCart';

import { FeaturedProductLabel } from './FeaturedProductLabel';

export function LatestProductCard({ product, principal = false, className }) {
  if (principal) {
    return (
      <div className={cn('relative group h-full overflow-hidden', className)}>
        <Link to={`/product/${product.handle}`} className='block size-full'>
          {product.featuredImage.url && (
            <img
              src={product.featuredImage.url}
              alt={product.featuredImage.altText}
              className='object-cover transition-transform duration-700 size-full group-hover:scale-105'
            />
          )}
          <div className='absolute inset-0 bg-gradient-to-t from-background/40 to-transparent opacity-60' />
        </Link>
        <div className='absolute pointer-events-none bottom-Sides left-Sides right-Sides md:bottom-12 md:left-12'>
          <FeaturedProductLabel className='pointer-events-auto' product={product} principal />
        </div>
      </div>
    );
  }

  return (
    <div className={cn('relative flex flex-col group transition-all duration-500', className)}>
      <Link
        to={`/product/${product.handle}`}
        className='block w-full aspect-[3/4] overflow-hidden rounded-sm bg-card border border-border/20 shadow-sm'>
        {product.featuredImage.url && (
          <img
            src={product.featuredImage.url}
            alt={product.featuredImage.altText}
            className='object-cover transition-transform duration-500 ease-out size-full group-hover:scale-110'
          />
        )}

        <div className='absolute bottom-6 left-1/2 -translate-x-1/2 w-[80%] opacity-0 group-hover:opacity-100 translate-y-4 group-hover:translate-y-0 transition-all duration-300 pointer-events-none group-hover:pointer-events-auto z-20'>
          <Suspense fallback={null}>
            <AddToCart
              product={product}
              variant='default'
              className='rounded-full bg-black text-white shadow-lg'
            />
          </Suspense>
        </div>
      </Link>

      <div className='flex flex-col gap-1 px-1 pt-6 text-left'>
        <Link
          to={`/product/${product.handle}`}
          className='font-serif text-xl font-black leading-tight truncate transition-opacity md:text-2xl text-primary hover:opacity-70'>
          {product.title}
        </Link>
        <p className='text-[10px] md:text-xs font-sans font-bold italic opacity-40 uppercase tracking-widest truncate'>
          {product.vendor}
        </p>
        <p className='mt-2 font-serif text-lg font-black text-primary'>
          {formatPrice(
            product.priceRange.minVariantPrice.amount,
            product.priceRange.minVariantPrice.currencyCode
          )}
        </p>
      </div>
    </div>
  );
}
