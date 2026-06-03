import { motion } from 'motion/react';
import { Suspense } from 'react';
import { Link } from 'react-router-dom';

import { formatPrice } from '@/lib/sfcc/utils';
import { cn } from '@/lib/utils';

import { AddToCart } from '../cart/AddToCart';
import { AddToWishlist } from '../wishlist/AddToWishlist';

const cardVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.18, ease: 'easeOut' } },
};

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
              referrerpolicy='no-referrer'
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
    <motion.div
      variants={cardVariants}
      whileHover={{ y: -6 }}
      transition={{ type: 'spring', stiffness: 300, damping: 18 }}
      className={cn('relative flex flex-col group transition-all duration-500', className)}>
      <Link
        to={`/product/${product.handle}`}
        className='block w-full aspect-[3/4] overflow-hidden rounded-sm bg-gray-100 border border-gray-200 shadow-sm'>
        {product.featuredImage.url && (
          <motion.img
            src={product.featuredImage.url}
            alt={product.featuredImage.altText}
            referrerpolicy='no-referrer'
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className='object-contain transition-transform duration-500 ease-out size-full group-hover:scale-110'
          />
        )}

        <div className='absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none group-hover:pointer-events-auto z-30'>
          <Suspense fallback={null}>
            <AddToCart
              product={product}
              variant='default'
              className='w-36 h-10 rounded-full bg-black text-white text-sm shadow-lg hover:bg-white hover:text-black'
            />
            <AddToWishlist
              bookId={product.id}
              size='sm'
              className='bg-black text-white shadow-lg hover:bg-white hover:text-black'
            />
          </Suspense>
        </div>
      </Link>

      <div className='flex flex-col gap-1 px-1 pt-6 text-left'>
        <Link
          to={`/product/${product.handle}`}
          className='font-sans text-lg font-semibold leading-tight truncate transition-opacity md:text-xl text-black'>
          {product.title}
        </Link>
        <p className='text-[10px] md:text-xs font-sans font-bold text-gray-500 uppercase tracking-widest truncate'>
          {product.vendor}
        </p>
        <p className='mt-2 font-sans text-base font-semibold text-black'>
          {formatPrice(
            product.priceRange.minVariantPrice.amount,
            product.priceRange.minVariantPrice.currencyCode
          )}
        </p>
      </div>
    </motion.div>
  );
}
