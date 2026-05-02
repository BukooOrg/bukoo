import { Suspense } from 'react';
import { Link } from 'react-router-dom';

import { formatPrice } from '@/lib/sfcc/utils';
import { cn } from '@/lib/utils';

import { AddToCart } from '../cart/add-to-cart';

import { FeaturedProductLabel } from './featured-product-label';

export function LatestProductCard({ product, principal = false, className }) {
  if (principal) {
    return (
      <div className={cn('relative group h-full overflow-hidden', className)}>
        <Link to={`/product/${product.handle}`} className='size-full block'>
          <img
            src={product.featuredImage.url}
            alt={product.featuredImage.altText}
            className='object-cover size-full group-hover:scale-105 transition-transform duration-700'
          />
          <div className='absolute inset-0 bg-gradient-to-t from-background/40 to-transparent opacity-60' />
        </Link>
        <div className='absolute bottom-Sides left-Sides right-Sides md:bottom-12 md:left-12 pointer-events-none'>
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
        <img
          src={product.featuredImage.url}
          alt={product.featuredImage.altText}
          className='object-cover size-full transition-transform duration-500 ease-out group-hover:scale-110'
        />

        <div className='absolute bottom-6 left-1/2 -translate-x-1/2 w-[80%] opacity-0 group-hover:opacity-100 translate-y-4 group-hover:translate-y-0 transition-all duration-300 pointer-events-none group-hover:pointer-events-auto'>
          <Suspense fallback={null}>
            <div className='p-1 bg-card/60 backdrop-blur-xl rounded-full border border-border/30 shadow-2xl overflow-hidden'>
              <AddToCart
                product={product}
                variant='default'
                className='rounded-full bg-primary text-background hover:scale-[1.02] active:scale-[0.98] transition-all'
              />
            </div>
          </Suspense>
        </div>
      </Link>

      <div className='pt-6 flex flex-col gap-1 text-left px-1'>
        <Link
          to={`/product/${product.handle}`}
          className='text-xl md:text-2xl font-serif font-black text-primary leading-tight hover:opacity-70 transition-opacity truncate'>
          {product.title}
        </Link>
        <p className='text-[10px] md:text-xs font-sans font-bold italic opacity-40 uppercase tracking-widest truncate'>
          {product.vendor}
        </p>
        <p className='text-lg font-serif font-black text-primary mt-2'>
          {formatPrice(
            product.priceRange.minVariantPrice.amount,
            product.priceRange.minVariantPrice.currencyCode
          )}
        </p>
      </div>
    </div>
  );
}
